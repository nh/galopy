$().ready(function() {
    $('a.update').mousedown(function() {
        var link = $(this);
        var progress = setInterval(function() { link.load("/status"); }, 500);
        $.get(link.attr("href"),function(){
            clearInterval(progress);
            link.text("Done");
        });
        return false;
    }).click(function(){return false;});
});
