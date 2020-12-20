$(function () {
    // $(document).ready(function() {
    //     let doc_extension = ['docx', 'doc']
    //     $('.image-wrapper').each(function(position, image_wrapper) {
    //         let full_path = $(image_wrapper).data('filepath')
    //         let extension = full_path.split(/[#?]/)[0].split('.').pop().trim()
    //         let image_preview = $(image_wrapper).find('.image-preview')[0]
    //
    //         if (doc_extension.includes(extension)) {
    //             // let media_path = full_path.split(/[#?]/)[0].split('/').slice(0, 3).join('/')
    //             $(image_preview).attr('src', '/static/image/doc.png')
    //         }
    //     });
    // });

    function getCookie(c_name) {
        if (document.cookie.length > 0) {
            var c_start = document.cookie.indexOf(c_name + "=");
            if (c_start !== -1) {
                c_start = c_start + c_name.length + 1;
                var c_end = document.cookie.indexOf(";", c_start);
                if (c_end === -1) c_end = document.cookie.length;

                return unescape(document.cookie.substring(c_start, c_end));
            }
        }

        return "";
    }

    function getCheckedCount() {
        return $('input[type="checkbox"][class="file-checkbox"]:checked').length
    }

    function setSelectAllStateButton() {
        $('.delete-selected').css('display', 'none')
        $(".select-all")[0].checked = false;

        $('.download-selected').css('display', 'none')
    }

    function setUnselectAllStateButton() {
        $('.delete-selected').css('display', 'inline-block')
        $(".select-all")[0].checked = true;

        $('.download-selected').css('display', 'inline-block')
    }

    $(".select-all").click(function () {
        let checkboxes_count = $('input[type="checkbox"][class="file-checkbox"]').length
        console.log(checkboxes_count)
        let checked_count = getCheckedCount()

        if (checkboxes_count !== checked_count && checked_count === 0) {
            check = true

            setUnselectAllStateButton()
        } else {
            check = false

            setSelectAllStateButton()
        }

        let inputs = $("input[type='checkbox'][class='file-checkbox']");
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].checked = check;
        }
    });

    $(".file-checkbox").click(function() {
        let checked_count = getCheckedCount()

        if (checked_count === 1) {
            setUnselectAllStateButton()
        } else if (checked_count === 0) {
            setSelectAllStateButton()
        }
    });

    $(".delete-selected").click(function () {
        let checked_inputs = $("input[type='checkbox'][class='file-checkbox']:checked");
        var files_id_to_delete = [];

        for (var i = 0; i < checked_inputs.length; i++) {
            files_id_to_delete.push(checked_inputs[i].value)
        }

        let count_checked = getCheckedCount();

        if (count_checked === 1) {
            res = confirm("Are you sure you want to delete these product?");
        } else {
            res = confirm("Are you sure you want to delete these products?");
        }

        if (res) {
            $.ajaxSetup({
                data: {files_id: JSON.stringify(files_id_to_delete), csrfmiddlewaretoken: getCookie("csrftoken")},
                headers: {"X-CSRFToken": getCookie("csrftoken")}
            });

            $.post("/storage/remove-file", function (result) {
            });

            setSelectAllStateButton()

            for (var i = 0; i < checked_inputs.length; i++) {
                checked_inputs[i].closest('tr').remove();
            }
        }
    });

    $(".i-delete").click(function () {
        let res = confirm("Are you sure you want to delete these product?")

        if (res) {
            let file_id = $($(this)[0]).data('file-id')

            $.ajaxSetup({
                data: {file_id: file_id, csrfmiddlewaretoken: getCookie("csrftoken")},
                headers: {"X-CSRFToken": getCookie("csrftoken")}
            });

            $.post("/storage/remove-file", function (result) {
            });

            $(this).closest('tr').remove();
        }
    });

    $(".download-selected").click(function () {
        let checked_inputs = $("input[type='checkbox'][class='file-checkbox']:checked");
        var files_id_to_download = [];

        for (var i = 0; i < checked_inputs.length; i++) {
            files_id_to_download.push(checked_inputs[i].value)
        }

        $.ajax({
            type: 'POST',
            url: "/storage/download-selected-files",
            data: {files_id: JSON.stringify(files_id_to_download), csrfmiddlewaretoken: getCookie("csrftoken")},
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            xhrFields:{
                responseType: 'blob'
            },
            success: function(response, status, xhr) {
                var link = document.createElement('a');

                link.href = window.URL.createObjectURL(response);
                link.download = xhr.getResponseHeader('Content-Disposition').split("filename=")[1];
                link.click();
            }
        })
    });
});