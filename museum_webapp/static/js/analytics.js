/*** 
 * 
 * 
*/

// a default object to be stored
const defaultPageAnalyticsObj = {
    'page_id': 0, 'hiddenTime': 0, 'visibilityChanges': 0,
    'dwellTime': 0, 'dwellMinusHidden': 0, 'startTimestamp': new Date(), 
};

/**
 * 
 * @param {string} key 
 * @param {object} value 
 * @param {boolean} increment 
 */
function updateValueInSession(key, value, increment = false, update = False) {
    storedData = JSON.parse(sessionStorage.getItem('pageAnalytics'));
    if (increment) {
        storedData[key] = storedData[key] + value;
    } else if (update) {
        storedData[key] += value;
    } else {
        storedData[key] = value;
    }
    sessionStorage.setItem('pageAnalytics', JSON.stringify(storedData));
}

// ---- PAGE VISIBILITY CHANGES ----
/**
 * 
 * @param isHidden 
 */
function handleVisibilityChange(isHidden) { 
    if (isHidden) {
        hiddenTimestamp = new Date();
    } else {
        updateValueInSession(
            'hiddenTime', (new Date() - hiddenTimestamp) / 1000, false, true 
        );
        updateValueInSession('visibilityChanges', 1, true, false);
    }
}

document.addEventListener('visibilitychange', function () {
    handleVisibilityChange(document.hidden)
}, false);
// --------------------------------

// ---- TODO ----

// --------------

window.addEventListener('load', (event) => {
    if (sessionStorage.getItem('pageAnalytics') == null) {
        defaultPageAnalyticsObj['page_id'] = page_id;
        sessionStorage.setItem('pageAnalytics', JSON.stringify(defaultPageAnalyticsObj));
    } else {
        // when the page loads, reset the session storage and send what's stored in there to db
        storedPageAnalytics = JSON.parse(sessionStorage.getItem('pageAnalytics'));
        storedPageAnalytics['csrfmiddlewaretoken'] = Cookies.get('csrftoken');
        
        // calculate dwell time, on the fly
        dwellTime = (new Date() - new Date(storedPageAnalytics['startTimestamp'])) / 1000;
        storedPageAnalytics['dwellTime'] = dwellTime;
        storedPageAnalytics['dwellMinusHidden'] = dwellTime - storedPageAnalytics['hiddenTime'];

        $.ajax({
            type: "POST",
            url: "logger/page/",
            data: storedPageAnalytics,
            fail: function () { console.log('posting page analytics failed'); }
        });

        defaultPageAnalyticsObj['page_id'] = page_id;
        sessionStorage.setItem('pageAnalytics', JSON.stringify(defaultPageAnalyticsObj));
    }
});

// Need to think about how we can capture client-side analytics
/* 
    Need to think about how we can capture client-side analytics:
        - Do we log summary analytics with each page?

    Pause events: capturing pauses between interactions (raw number, categorised later)
    Scrolling: the amount of scrolling that happens on a page?
    
*/