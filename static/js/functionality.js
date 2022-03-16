// https://stackoverflow.com/questions/43043113/how-to-force-reloading-a-page-when-using-browser-back-button/56851042#56851042
var perfEntries = performance.getEntriesByType('navigation');

if (perfEntries[0].type == 'back_forward') {
    location.reload(true)
}