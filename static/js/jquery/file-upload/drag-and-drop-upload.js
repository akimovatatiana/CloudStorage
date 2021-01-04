$(function () {
  $(".js-upload-files").click(function () {
    $("#fileupload").click();
  });

  $("#fileupload").fileupload({
    dataType: 'json'
  }).bind('fileuploadstop', function (e) {
        location.reload();
    });

});