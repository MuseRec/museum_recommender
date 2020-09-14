function interaction_event(event_type, content_id, page_id, csrf_token) {
    $.ajax({
        type: "POST",
        url: "logger/log/",
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

