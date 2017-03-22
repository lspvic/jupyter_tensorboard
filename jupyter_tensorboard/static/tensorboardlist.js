define([
    'jquery',
    'base/js/namespace',
    'base/js/utils',
    'tree/js/notebooklist',
], function($, Jupyter, utils, notebooklist) {
    "use strict";
    
    var TensorboardList = function (selector, options) {
        this.base_url = Jupyter.notebook_list.base_url;
        this.init_elements();
        this.element_name = options.element_name || 'running';
        this.selector = selector;
        this.tensorboads = [];
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
            this.load_tensorboards();
        }
    };

    TensorboardList.prototype = Object.create(notebooklist.NotebookList.prototype);

    TensorboardList.prototype.init_elements = function(){
        // link nbextension css file
        var static_url = this.base_url + "nbextensions/jupyter_tensorboard/";
        $('head').append(
            $('<link>')
            .attr('rel', 'stylesheet')
            .attr('type', 'text/css')
            .attr('href', static_url + 'style.css')
        );
        
        // tensorboad running list panel
        $("#accordion").append('<div class="panel panel-default">\
              <div class="panel-heading">\
                <a data-toggle="collapse" data-target="#collapseTensorboard" href="#">\
                  Tensorboard Instances\
                </a>\
              </div>\
              <div id="collapseTensorboard" class="collapse in">\
                <div class="panel-body">\
                  <div id="tensorboard_list">\
                    <div id="tensorboard_list_header" class="row list_placeholder">\
                      <div> There are no tensorboard instances running. </div>\
                    </div>\
                  </div>\
                </div>\
              </div>\
            </div>');
        
        // new tensorboard menu on current directory
        $("#new-menu").append('<li role="presentation" id="new-tensorboard">\
                <a role="menuitem" tabindex="-1" href="#">Tensorboard</a>\
            </li>');
            
        // tensorboard button when select a directory
        $(".dynamic-buttons:first").append('<button id="#tensorboard-button" title="Create Tensorboard Instance with selected logdir"  class="tensorboard-button btn btn-default btn-xs">Tensorboard</button>');
    };
    
    TensorboardList.prototype.bind_events = function () {
        var that = this;
        $('#refresh_running_list').click(function () {
            that.load_tensorboards();
        });
        $('#new-tensorboard').click($.proxy(function(){
            that.new_tensorboard(Jupyter.notebook_list.notebook_path);
        }, this));
        $(".tensorboard-button").click($.proxy(function(){
            that.new_tensorboard(Jupyter.notebook_list.selected[0].path);
        }, this));
    };

    TensorboardList.prototype.new_tensorboard = function (logdir) {
            var that = this;
            var settings = {
                type : "POST",
                contentType: "application/json",
                data: '{"logdir":"' + logdir + '"}',
                dataType: "json",
                success : function (data, status, xhr) {
                    that.load_tensorboards();
                    var name = data.name;
                    var loc = utils.url_path_join(that.base_url, 'tensorboard', 
                        utils.encode_uri_components(name)) + "/";
                    var win = window.open(loc, 'tensorboard' + name);
                },
                error : function(jqXHR, status, error){
                    //w.close();
                    utils.log_ajax_error(jqXHR, status, error);
                },
            };
            var url = utils.url_path_join(this.base_url, 'api/tensorboard');
            utils.ajax(url, settings);
            
            var list_items = $('.list_item');
            for (var i=0; i<list_items.length; i++) {
                var $list_item = $(list_items[i]);
                if ($list_item.data('path') === logdir) {
                    $list_item.find('input[type=checkbox]').prop('checked', false);
                    break;
                }
            }
            Jupyter.notebook_list._selection_changed();
    };
    
    TensorboardList.prototype.load_tensorboards = function() {
        var url = utils.url_path_join(this.base_url, 'api/tensorboard');
        utils.ajax(url, {
            type: "GET",
            cache: false,
            dataType: "json",
            success: $.proxy(this.tensorboards_loaded, this),
            error : utils.log_ajax_error
        });
    };

    TensorboardList.prototype.tensorboards_loaded = function (data) {
        this.tensorboads = data;
        this.clear_list();
        var item, term;
        for (var i=0; i < this.tensorboads.length; i++) {
            term = this.tensorboads[i];
            item = this.new_item(-1);
            this.add_link(term.name, item);
            this.add_logdir(term.logdir, item);
            this.add_shutdown_button(term.name, item);
        }
        $('#tensorboard_list_header').toggle(data.length === 0);
    };
    
    TensorboardList.prototype.add_link = function(name, item) {
        item.data('term-name', name);
        item.find(".item_name").text("tensorboard/" + name + "/");
        item.find(".item_icon").addClass("fa fa-tensorboard");
        var link = item.find("a.item_link")
            .attr('href', utils.url_path_join(this.base_url, "tensorboard",
                utils.encode_uri_components(name), "/"));
        //link.attr('target', IPython._target||'_blank');
        link.attr('target', 'tensorboard' + name);
        this.add_shutdown_button(name, item);
    };
    
    TensorboardList.prototype.add_logdir = function(logdir, item){
            var running_indicator = item.find(".item_buttons").text('');
            var kernel_name = $('<div/>')
                .addClass('kernel-name')
                .text(logdir)
                .appendTo(running_indicator);
    };
    
    TensorboardList.prototype.add_shutdown_button = function(name, item) {
        var that = this;
        var shutdown_button = $("<button/>").text("Shutdown").addClass("btn btn-xs btn-warning").
            click(function (e) {
                var settings = {
                    processData : false,
                    type : "DELETE",
                    dataType : "json",
                    success : function () {
                        that.load_tensorboards();
                    },
                    error : utils.log_ajax_error,
                };
                var url = utils.url_path_join(that.base_url, 'api/tensorboard',
                    utils.encode_uri_components(name));
                utils.ajax(url, settings);
                return false;
            });
        item.find(".item_buttons").append(shutdown_button);
    };

    return {TensorboardList: TensorboardList};
});
