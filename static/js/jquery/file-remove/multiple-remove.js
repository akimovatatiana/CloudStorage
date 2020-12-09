$(function () {
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
        return $('input[type="checkbox"]:checked').length
    }

    $(".select-all").click(function () {
        let checkboxes_count = $('input[type="checkbox"]').length
        let inputs = $("input[type='checkbox']");

        let checked_count = getCheckedCount()
        if (checkboxes_count !== checked_count) {
            state = false
            display = 'none'
            label = 'Select all'

            if (checked_count === 0) {
                state = true
                display = 'inline-block'
                label = 'Unselect all'
            }

            for (var i = 0; i < inputs.length; i++) {
                inputs[i].checked = state;
            }

            $('.delete-selected').css('display', display)
            $('.btn-select-all').html(label)
        } else {
            // Unselect all
            for (var i = 0; i < inputs.length; i++) {
                inputs[i].checked = false;
            }

            $('.delete-selected').css('display', 'none')
            $('.btn-select-all').html("Select all")
        }
    });

    $(".file-checkbox").click(function () {
        let checkboxes_count = $('input[type="checkbox"]').length
        let checked_count = getCheckedCount()

        if (checked_count === 1) {
            $('.delete-selected').css('display', 'inline-block')
            $('.btn-select-all').html('Unselect all')
        } else if (checked_count === 0) {
            $('.btn-select-all').html("Select all")
            $('.delete-selected').css('display', 'none')
        }

        // if (checked_count !== checkboxes_count) {
        //     $('.btn-select-all').html('Select all')
        // }
    });

    $(".delete-selected").click(function () {
        let checked_inputs = $("input[type='checkbox']:checked");
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

            for (var i = 0; i < checked_inputs.length; i++) {
                checked_inputs[i].closest('tr').remove();
            }
        }
    })

    $(".btn-delete").click(function () {
        let res = confirm("Are you sure you want to delete these product?")

        if (res) {
            let file_id = $(".btn-delete")[0].value

            $.ajaxSetup({
                data: {file_id: file_id, csrfmiddlewaretoken: getCookie("csrftoken")},
                headers: {"X-CSRFToken": getCookie("csrftoken")}
            });

            $.post("/storage/remove-file", function (result) {
            });

            $(this).closest('tr').remove();
        }
    });
});