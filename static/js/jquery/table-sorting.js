jQuery.fn.dataTable.ext.type.order['file-size-pre'] = function (data) {
    var matches = data.match(/^(\d+(?:\.\d+)?)\s*([a-z]+)/i);
    var multipliers = {
        b: 1,
        bytes: 1,
        kb: 1000,
        kib: 1024,
        mb: 1000000,
        mib: 1048576,
        gb: 1000000000,
        gib: 1073741824,
        tb: 1000000000000,
        tib: 1099511627776,
        pb: 1000000000000000,
        pib: 1125899906842624
    };

    if (matches) {
        var multiplier = multipliers[matches[2].toLowerCase()];
        console.log('true')
        return parseFloat(matches[1]) * multiplier;
    } else {
        console.log('false')
        return -1;
    }
    ;
};

$(document).ready(function () {
    $('#files-list').DataTable({
        order: [[2, false]],
        columnDefs: [
            {targets: [0, 1, -1], orderable: false, visibility: false},
            {targets: [0, 1, 3, 4, 5, 6], searchable: false},
            {type: 'file-size', targets: 5}
        ],
    }, {
            "aoColumnDefs": [
      { "bSortable": false, "aTargets": [ 0 ] }
    ]
    });
});