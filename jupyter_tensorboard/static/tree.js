define(["jquery",
    "base/js/namespace",
     "tree/js/sessionlist",
    "./tensorboardlist",
    ], function($, Jupyter, sessionlist, tensorboardlist){
        
    function load_ipython_extension(){
        
        var tensorboard_list = new tensorboardlist.TensorboardList("#tensorboard_list", {});
        
        var _selection_changed = Jupyter.notebook_list.__proto__._selection_changed;
        Jupyter.notebook_list.__proto__._selection_changed = function(){
            _selection_changed.apply(this);
            selected = this.selected;
            if(selected.length == 1 && selected[0].type === 'directory'){
                $('.tensorboard-button').css('display', 'inline-block');
            } else {
                $('.tensorboard-button').css('display', 'none');
            }
        };
        Jupyter.notebook_list._selection_changed();
        
        $('#running .panel-group .panel .panel-heading a').each(function(index, el) {
            $('.fa.fa-caret-down').remove();
        });
        var session_list = new sessionlist.SesssionList({events: null});
    }

    return {
        load_ipython_extension: load_ipython_extension
    };
});