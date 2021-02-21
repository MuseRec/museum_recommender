/**
 * A function to post the interaction events to the backend when they happen. These events log
 * the user interaciton with the website and the artwork.
 * @param {string} event_type   the type of event that occurred
 * @param {string} content_id   the piece of content that it occurred on, i.e. art id clicked on
 * @param {string} page_id      the page that the event occurred on, i.e. index
 * @param {string} csrf_token   cross-site security token, required to post to the backend.
 */
function interaction_event(event_type, content_id, page_id, csrf_token) {
    $.ajax({
        type: "POST",
        url: "logger/log/", // corresponds to the log view in collector.views
        data: {
            "csrfmiddlewaretoken": csrf_token,
            "event_type": event_type, 
            "content_id": content_id, 
            "page_id": page_id 
        },
        fail: function() {
            console.log('interaction log failed (' + event_type + ')')
        }
    });
};

