import io

import pandas as pd
import numpy as np
import regex as re
import csv
import unittest
import os
# noinspection PyCompatibility
from collections.abc import Collection
from os.path import join, exists
from datetime import date
from functools import reduce, partial
from typing import Tuple, TextIO
# noinspection PyUnresolvedReferences
from pprint import pprint


mapper = {
    chr(8210): "-",
    chr(8211): "-",
    chr(8212): "-",
    r"later": "late",
    r"latest": "late",
    r"earlier": "early",
    r"earliest": "early",
    r"\s{2,}": " ",
    r"(?<=mid|early|late)-(?=\d+)": " ",
    r"/": "-",
    r"[-]{2,}": "-",
    # r"c\.": "",
    r"about": "",
    # r"(?<=\d+)s\b": "",
    r"(?<=early)[\s-]?mid": "",
}

csv_columns = [
    'Collection Name',
    'Artwork Classification',
    'Artwork Title',
    'Execution Date',
    'Earliest Date',
    'Latest Date',
    'Medium',
    'Artist Forename',
    'Artist Surname',
    'Artist Birth Date',
    'Artist Death Date',
    'Artist Active Dates',
    'Image Credit',
    'Linked Terms',
    'Linked Topics',
    'Linked Art Terms',
    'Filename',
    'Location',
]

db_columns = [
    'Collection Name',
    'Artwork Classification',
    'Artwork Title',
    'Medium',
    'Artist Name',
    'Artist Birth Date',
    'Artist Death Date',
    'Earliest Date',
    'Latest Date',
    'Image Credit',
    'Linked Terms',
    'Linked Topics',
    'Linked Art Terms',
    'Filename',
    'Location',
]

mv_columns = [
    'Artist Forename',
    'Artist Surname',
    'Artist Birth Date',
    'Artist Death Date',
]

delimiter = '|'


def __check_date(dat):
    try:
        dat = np.nan if np.isnan(dat) else date(dat, 1, 1)
    except ValueError:
        print("Cannot convert {0} to date".format(dat))
        return np.nan
    return dat


def execution_date_converter(val) -> Tuple[float, float] or None:
    def get_date(x):
        offset = (0, 0)
        if x.find("mid") != -1:
            offset = (30, 69)
        elif x.find("early") != -1:
            offset = (0, 39)
        elif x.find("late") != -1:
            offset = (60, 99)
        re_obj = re.search(r"\d+(?=st|nd|rd|th)", x)
        if re_obj:
            y = (int(re_obj.group(0)) - 1)*100
            return y + offset[0], y + offset[1]
        re_obj = re.search(r"\d{4}(?=s)", x)
        if re_obj:
            y = int(re_obj.group(0))
            return y, y + 9
        re_obj = re.search(r"\d{1,4}", x)
        if re_obj:
            y = int(re_obj.group(0))
            return y + offset[0], y + offset[1]
        return

    if val is None or \
            pd.isna(val) or \
            (isinstance(val, str) and len(val) == 0):
        return

    out = re.sub(r"\s{2,}", " ", val)
    out = reduce(lambda s, pos: re.sub(pos[0], pos[1], s), mapper.items(), out.lower())
    out = out.strip()

    years = list()
    for e in out.split("-"):
        dat = get_date(e)
        if dat is None or pd.isna(dat) or (isinstance(dat, str) and len(dat) == 0):
            years.append(None)
            continue
        years.append(dat)

    if years[0] is not None:
        years[0] = sorted(years[0])
        if years[-1] is None:
            return years[0]
        years[-1] = sorted(years[-1])
        if years[-1][1] < years[0][0]:
            p = np.power(10, np.ceil(np.log10(years[-1][1]))).astype(int)
            years[-1] = list(years[-1])
            years[-1][1] += int(years[0][0]/p)*p
        return years[0][0], years[-1][1]

    if years[-1] is None:
        return
    return years[-1]


def early_execution_date(dat) -> float or None:
    out = execution_date_converter(dat)
    if isinstance(out, Collection):
        out = list(out)[0]
    if out is None:
        return
    __check_date(out)
    return out


def late_execution_date(dat) -> float or None:
    out = execution_date_converter(dat)
    if isinstance(out, Collection) and len(out) > 1:
        out = list(out)[1]
    else:
        return
    __check_date(out)
    return out


def flatten(x) -> list:
    return reduce(list.__add__,
                  (list(items if isinstance(items, Collection) else [items]) for items in x))


def artuk_record_parser(file, folder=None, **kwargs) -> pd.DataFrame:
    # Returns a total number of records, excluding the row with column names
    def __row_count(cr):
        cr.seek(0)
        return sum(1 for _ in cr)

    # Skip first `st` number of rows
    def __skip(it, st):
        for _ in range(st):
            next(it)

    # Check if multiple values with single cells can be parsed
    def __is_parse(c):
        c = np.array(c)
        f = (c == 1) | (c == 0)
        if all(f):
            raise ValueError("Empty array")
        # noinspection PyTypeChecker
        return all(c[~f][1:] == c[~f][0])

    # Returns regular file reader
    def __artuk_reader(csv_f: TextIO):
        return csv.reader(csv_f, dialect='unix', delimiter=delimiter)

    # Returns DictReader. Keys refer to CSV column names
    def __artuk_dict_reader(csv_f: TextIO):
        return csv.DictReader(csv_f, dialect='unix', delimiter=delimiter)

    # Check if element is numeric
    def __convert_if_numeric(x: str) -> float or None:
        if x is None:
            return None
        re_res = re.search(r"[0-9]+", x)
        if re_res is None:
            return None
        return float(re_res.group(0))

    # Convert or NoneType objects to a numeric NaN
    def __return_nan(x, default=None) -> object or np.ndarray:
        default = np.nan if default is None else default
        return default if x is None else x

    # Return either element of a sequence, first element if len == 1 or None
    def __extract(dct, size, is_size, key, val) -> object or None:
        return None if not is_size[key] else dct[key][0] if size[key] == 1 else dct[key][val]

    # Default options
    folder = "" if folder is None else folder
    begin, end, offset = 0, np.inf, 0
    has_header, has_index = True, False
    verbose = False
    # Custom options
    if "begin" in kwargs:
        begin = kwargs["begin"]
    if "end" in kwargs:
        end = kwargs["end"]
    if "hasheader" in kwargs:
        has_header = kwargs["hasheader"]
    if "hasindex" in kwargs:
        has_index = kwargs["hasindex"]
    if "verbose" in kwargs:
        verbose = kwargs["verbose"]

    # CSV file requires a header
    if not has_header:
        raise ValueError("The CSV file has to have column names")

    # Logger skipped records
    skipped = list()

    # Parse CSV file
    with open(join(folder, file), newline='') as csv_reader:
        row_count = __row_count(csv_reader) - 1
        begin = max(0, min(row_count, begin))
        end = min(row_count, max(0, end))
        csv_reader.seek(0)
        reader = __artuk_dict_reader(csv_reader)
        __skip(reader, begin)

        idx = begin
        for csv_dict in reader:
            if idx > end - 1:
                break

            db_dict = dict()
            df = pd.DataFrame([], columns=db_columns)

            # Convert empty strings to None
            row_dict = {k: v if len(v) > 0 else None for k, v in csv_dict.items()}

            db_dict["Collection Name"] = row_dict["Collection Name"]
            db_dict["Artwork Classification"] = row_dict["Artwork Classification"]
            db_dict["Artwork Title"] = row_dict["Artwork Title"]
            db_dict["Medium"] = row_dict["Medium"]
            db_dict["Image Credit"] = row_dict["Image Credit"]
            db_dict["Linked Terms"] = row_dict["Linked Terms"]
            db_dict["Linked Topics"] = row_dict["Linked Topics"]
            db_dict["Linked Art Terms"] = row_dict["Linked Art Terms"]
            db_dict["Filename"] = row_dict["Filename"]
            db_dict["Location"] = row_dict["Location"]

            # Parse dates and convert them to Earliest and Latest dates
            e_date = row_dict["Earliest Date"]
            l_date = row_dict["Latest Date"]
            ex_date = np.array([
                e for e in flatten((
                    execution_date_converter(row_dict["Execution Date"]),
                    execution_date_converter(row_dict["Artist Active Dates"]),
                    None if e_date is None else float(e_date),
                    None if l_date is None else float(l_date),
                )) if e is not None
            ])
            # Convert dates to float values (including NaNs)
            db_dict["Earliest Date"] = __return_nan(ex_date.min(initial=None) if ex_date.size > 0 else None)
            db_dict["Latest Date"] = __return_nan(ex_date.max(initial=None) if ex_date.size > 0 else None)

            # CSV contains records with multiple entries within single cells
            if any(row_dict[e].find(";") != -1 for e in mv_columns if row_dict[e] is not None):
                values = {
                    k: [e.strip() for e in row_dict[k].split(";")] if row_dict[k] is not None else None
                    for k in mv_columns
                }
                lengths = {k: len(v) if v is not None else 0 for k, v in values.items()}
                n_lengths = np.array([v for _, v in lengths.items()])
                if not __is_parse(n_lengths):
                    skipped.append(row_dict)
                    if verbose:
                        print("Skipped {0} records".format(len(skipped)))
                    continue
                # noinspection PyTypeChecker
                if all(n_lengths[1:] == n_lengths[0]):
                    for i in range(n_lengths[0]):
                        db_dict["Artist Name"] = "{} {}".format(
                            values["Artist Forename"][i], values["Artist Surname"][i]
                        ).strip()
                        db_dict["Artist Birth Date"] = __return_nan(
                            __convert_if_numeric(values["Artist Birth Date"][i]))
                        db_dict["Artist Death Date"] = __return_nan(
                            __convert_if_numeric(values["Artist Death Date"][i]))
                        df = df.append(pd.DataFrame(db_dict, index=[idx + offset]))
                        offset += 1
                    yield df
                else:
                    is_length = {k: v > 0 for k, v in lengths.items()}
                    extract = partial(__extract, values, lengths, is_length)
                    for i in range(n_lengths.max(initial=0)):
                        db_dict["Artist Name"] = "{} {}".format(
                            extract("Artist Forename", i),
                            extract("Artist Surname", i),
                        ).strip()
                        db_dict["Artist Birth Date"] = __return_nan(
                            __convert_if_numeric(extract("Artist Birth Date", i))
                        )
                        db_dict["Artist Death Date"] = __return_nan(
                            __convert_if_numeric(extract("Artist Death Date", i))
                        )
                        df = df.append(pd.DataFrame(db_dict, index=[idx + offset]))
                        offset += 1
                    yield df
                offset -= 1
            else:
                # Executed when values are regular
                db_dict["Artist Name"] = "{} {}".format(
                    row_dict["Artist Forename"], row_dict["Artist Surname"]
                ).strip()
                db_dict["Artist Birth Date"] = __return_nan(__convert_if_numeric(row_dict["Artist Birth Date"]))
                db_dict["Artist Death Date"] = __return_nan(__convert_if_numeric(row_dict["Artist Death Date"]))
                yield pd.DataFrame(db_dict, index=[idx + offset])
            idx += 1
    if verbose:
        print(skipped)


# Tests
class TestArtUKReader(unittest.TestCase):
    old_umask = None
    # folder = "artwork_metadata"
    # csv_file = "ArtUK_main_sample.csv"
    header = "|".join([
        "Collection Name",
        "Artwork Classification",
        "Artwork Title",
        "Execution Date",
        "Earliest Date",
        "Latest Date",
        "Medium",
        "Artist Forename",
        "Artist Surname",
        "Artist Birth Date",
        "Artist Death Date",
        "Artist Active Dates",
        "Image Credit",
        "Linked Terms",
        "Linked Topics",
        "Linked Art Terms",
        "Filename",
    ])
    csv_tests = {
        "csv_regular": "|".join([
            "Leeds Museums",
            "Painting",
            "Landscape",
            "1869",
            "1869",
            "1869",
            "oil on canvas",
            "XXX",
            "AAA",
            "1815",
            "1893",
            "",
            "Leeds Museums and Galleries",
            "Branch, Sky, Landscape",
            "",
            "",
            "WYL_LMG_036_12-001.jpg",
        ]),
        "csv_mv_equal_length": "|".join([
            "Leeds Museums",
            "Painting",
            "Landscape",
            "1869",
            "1869",
            "1869",
            "oil on canvas",
            "XXX; YYY; ZZZ",
            "AAA; BBB; CCC",
            "1815; 1798; 1745",
            "1893; 1881; 1820",
            "",
            "Leeds Museums and Galleries",
            "Branch, Sky, Landscape",
            "",
            "",
            "WYL_LMG_036_12-001.jpg",
        ]),
        "csv_mv_not_equal_length1": "|".join([
            "Leeds Museums",
            "Painting",
            "Landscape",
            "1869",
            "1869",
            "1869",
            "oil on canvas",
            "XXX; YYY; ZZZ",
            "AAA; BBB; CCC",
            "1815",
            "1893",
            "",
            "Leeds Museums and Galleries",
            "Branch, Sky, Landscape",
            "",
            "",
            "WYL_LMG_036_12-001.jpg",
        ]),
        "csv_mv_not_equal_length2": "|".join([
            "Leeds Museums",
            "Painting",
            "Landscape",
            "1869",
            "1869",
            "1869",
            "oil on canvas",
            "XXX",
            "AAA",
            "1815; 1798",
            "1893",
            "",
            "Leeds Museums and Galleries",
            "Branch, Sky, Landscape",
            "",
            "",
            "WYL_LMG_036_12-001.jpg",
        ]),
        "csv_mv_not_equal_length3": "|".join([
            "Leeds Museums",
            "Painting",
            "Landscape",
            "1869",
            "1869",
            "1869",
            "oil on canvas",
            "XXX",
            "AAA",
            "1815",
            "1893; 1881; 1901; 1905",
            "",
            "Leeds Museums and Galleries",
            "Branch, Sky, Landscape",
            "",
            "",
            "WYL_LMG_036_12-001.jpg",
        ]),
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.old_umask = os.umask(0o077)
        print("\nCreating csv test files")
        for k, v in cls.csv_tests.items():
            with open(k + ".csv", "w") as csv_file:
                csv_file.write(cls.header + "\n" + cls.csv_tests[k] + "\n")
        cls.test_files = [k for k, _ in cls.csv_tests.items()]

    @classmethod
    def tearDownClass(cls) -> None:
        print("\nRemoving csv test files")
        for k, _ in cls.csv_tests.items():
            os.remove(k + ".csv")
        os.umask(cls.old_umask)

    @staticmethod
    def return_df(file):
        csv_iter = artuk_record_parser(file)
        return next(csv_iter)

    # def testCsvFileExists(self):
    #     the_file = join(self.folder, self.csv_file)
    #     self.assertTrue(exists(the_file), msg="Missing {}".format(the_file))

    # Test of correct names
    def testRegularRecord(self):
        df = TestArtUKReader.return_df(self.test_files[0] + ".csv")
        # print(df.loc[:, ["Artist Name", "Artist Birth Date", "Artist Death Date"]])
        self.assertTrue(df.shape == (1, 14), "Wrong # of columns")
        self.assertTrue(df.loc[0, "Artist Name"] == "XXX AAA")

    # Test of multiple entries whose a number of elements is the same across
    # multiple cells
    def testMultipleRecordEqualLength(self):
        df = TestArtUKReader.return_df(self.test_files[1] + ".csv")
        self.assertTrue(df.shape == (3, 14), "Wrong # of columns")
        self.assertEqual(
            tuple(df.loc[0, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1893.0)
        )
        self.assertEqual(
            tuple(df.loc[1, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("YYY BBB", 1798.0, 1881.0)
        )
        self.assertEqual(
            tuple(df.loc[2, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("ZZZ CCC", 1745.0, 1820.0)
        )

    # Tests of multiple entries whose a number of elements is not the same across
    # multiple cells.
    def testMultipleRecordNotEqualLength1(self):
        df = TestArtUKReader.return_df(self.test_files[2] + ".csv")
        # print(df.loc[:, ["Artist Name", "Artist Birth Date", "Artist Death Date"]])
        self.assertTrue(df.shape == (3, 14), "Wrong # of columns")
        self.assertEqual(
            tuple(df.loc[0, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1893.0)
        )
        self.assertEqual(
            tuple(df.loc[1, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("YYY BBB", 1815.0, 1893.0)
        )
        self.assertEqual(
            tuple(df.loc[2, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("ZZZ CCC", 1815.0, 1893.0)
        )

    def testMultipleRecordNotEqualLength2(self):
        df = TestArtUKReader.return_df(self.test_files[3] + ".csv")
        # print(df.loc[:, ["Artist Name", "Artist Birth Date", "Artist Death Date"]])
        self.assertTrue(df.shape == (2, 14), "Wrong # of columns")
        self.assertEqual(
            tuple(df.loc[0, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1893.0)
        )
        self.assertEqual(
            tuple(df.loc[1, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1798.0, 1893.0)
        )

    def testMultipleRecordNotEqualLength3(self):
        df = TestArtUKReader.return_df(self.test_files[4] + ".csv")
        # print(df.loc[:, ["Artist Name", "Artist Birth Date", "Artist Death Date"]])
        self.assertTrue(df.shape == (4, 14), "Wrong # of columns")
        self.assertEqual(
            tuple(df.loc[0, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1893.0)
        )
        self.assertEqual(
            tuple(df.loc[1, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1881.0)
        )
        self.assertEqual(
            tuple(df.loc[2, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1901.0)
        )
        self.assertEqual(
            tuple(df.loc[3, ["Artist Name", "Artist Birth Date", "Artist Death Date"]]),
            ("XXX AAA", 1815.0, 1905.0)
        )
