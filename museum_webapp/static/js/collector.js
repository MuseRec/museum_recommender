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
        // url: "interaction_logger",
        url: "/logger/log/", // corresponds to the log view in collector.views
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

/**
 * A function to save the artwork ratings that the user assigns. We do not want to reload
 * the page each time this happens, so we'll send it to the server via an ajax call.
 */
function rating_event(artwork_id, rating_number, csrf_token) {
    $.ajax({
        type: "POST",
        url: "/rating/",
        data: {
            "csrfmiddlewaretoken": csrf_token,
            "artwork_id": artwork_id,
            "rating_number": rating_number
        },
        fail: function() {
            console.log('rating log failed (' + artwork_id + ')')
        }
    });
}

/**
 * A function to save the selected image by the participant. This is trigged when
 * they click submit on the artwork inline form
 */
function save_selected_artwork(artwork_id, selection_context, select_or_deselect, csrf_token) {
    $.ajax({
        type: "POST",
        url: "/selected/",
        data: {
            "csrfmiddlewaretoken": csrf_token,
            "artwork_id": artwork_id,
            "selection_context": selection_context,
            "select_or_deselect": select_or_deselect
        },
        success: function(data) {
            $('#selected-btn').value('Selected!');
        },
        error: function(response) {
            console.log('THIS IS THE RESPONSE: ' + response)
        },
        fail: function() {
            console.log('saving selected artwork failed (' + artwork_id + ')');
        }
    });
}

/**
 * A function to transition to the next stage of the study
 */
function study_transition(csrf_token) {
    $.ajax({
        type: "POST",
        url: "/transition/",
        data: {
            "csrfmiddlewaretoken": csrf_token
        }
    });
}