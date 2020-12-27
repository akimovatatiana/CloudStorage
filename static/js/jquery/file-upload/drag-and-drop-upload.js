$(function () {

  $(".js-upload-files").click(function () {
    $("#fileupload").click();
  });

  $("#fileupload").fileupload({
    dataType: 'json',
    done: function (e, data) {
      if (data.result.is_valid) {
        // console.log(data.result['size'])
        window.location.replace('/storage/overview')
        // $("#files-list tbody").prepend(
        //   "<tr>" +
        //     "<td><input type='checkbox' class='file-checkbox' value='{{ file.id }}' name='file-check' id='file-check-id'></td>" +
        //     "<td>" +
        //       "<div class='image-wrapper' data-filepath='{{ file.file.url }}'>" +
        //         "<img class='image-preview' src='../../../image/default-file-icon.gif'/>" +
        //     "</td>" +
        //     "<td><a href='" + data.result.url + "'>" + data.result.name + "</a></td>" +
        //     "</tr>"
        // )
      }
    }
  });

});