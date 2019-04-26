define([
    'jquery',
    'base/js/namespace',
    'base/js/dialog',
    'base/js/utils',
    'tree/js/notebooklist',
], function($, Jupyter, dialog, utils, notebooklist) {
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

    var help_information = ["Check that tensorflow(-gpu)>=1.3 is installed.",
        "Check that jupyter, tensorflow and jupyter_tensorboard have the same python version.",
        "Check that jupyter_tensorboard is installed via pip list. If you want uninstall this extension, run <span>jupyter nbextension disable jupyter_tensorboard/tree --user</span> and <span>jupyter nbextension uninstall jupyter_tensorboard --user</span>;",
        "Copy your browser console logs to submit a new issue in <a href='https://github.com/lspvic/jupyter_tensorboard'>https://github.com/lspvic/jupyter_tensorboard</a>",
    ];
    var ajax_error = function(){
        dialog.modal({
            title : 'Jupyter tensorboard extension error',
            body : "<ol>" + help_information.map(function(ele){return "<li>" + ele + "</li>";}).join("") + "</ol>",
            sanitize: false,
            buttons: {'OK': {'class' : 'btn-primary'}},
            notebook: Jupyter.notebook,
            keyboard_manager: Jupyter.keyboard_manager,
        });
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
        $("#new-menu").append('<li role="presentation" class="dropdown-submenu dropleft">\
                <a role="menuitem" tabindex="-1" href="#">Tensorboard...</a>\
                <ul class="dropdown-menu" style="right:100%;left:-100%">\
                  <li id="new-tensorboard"><a>Current directory</a></li>\
                  <li id="new-tensorboard-custom"><a>Custom directory...</a></li>\
                </ul>\
            </li>');

        // tensorboard button when select a directory
        $(".dynamic-buttons:first").append('<button id="#tensorboard-button"\
            title="Create Tensorboard Instance with selected logdir"\
            class="tensorboard-button btn btn-default btn-xs">Tensorboard</button>');
    };

    TensorboardList.prototype.bind_events = function () {
        var that = this;

        $('#refresh_running_list').click(function () {
            that.load_tensorboards();
        });
        $('#new-tensorboard').click($.proxy(function(){
            that.new_tensorboard(Jupyter.notebook_list.notebook_path);
        }, this));
        $('#new-tensorboard-custom').click(function () {
            that.dir_selection_dialog();
        });
        $(".tensorboard-button").click($.proxy(function(){
            that.new_tensorboard(Jupyter.notebook_list.selected[0].path);
        }, this));
    };

    TensorboardList.prototype.dir_selection_dialog = function() {
        var that = this;
        dialog.modal({
            title : 'Specify a log directory',
            body : '<div class="form-group">\
              <input id="tensorboard-dir-input" class="form-control" type="text" placeholder="Type path to directory"/>\
              <small class="form-text text-muted">Specify a relative or absolute path</small>\
            </div>',
            sanitize: false,
            buttons: {
                'Cancel': {'class' : 'btn-secondary'},
                'OK': {
                    'class': 'btn-primary',
                    'id': 'new-tensorboard-custom-submit',
                    'click': function() {
                        that.new_tensorboard($('#tensorboard-dir-input').val());
                    }
                }
            },
            notebook: Jupyter.notebook,
            keyboard_manager: Jupyter.keyboard_manager
        });
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
                error: ajax_error,
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
            statusCode: {
                404: function(){
                    $("#tensorboard_list_header").html("<div>Jupyter tensorboard extension error<div style='font-weight:normal;'><ol style='margin-top:13px;padding-left:20px;'>" + help_information.map(function(ele){return "<li>" + ele + "</li>";}).join("") + "</ol></div></div>")
                }
            }
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
            this.add_reload_time(term.reload_time, item);
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
    };

    TensorboardList.prototype.add_logdir = function(logdir, item){
        var running_indicator = item.find(".item_buttons").text('');
        var kernel_name = $('<div/>')
            .addClass('kernel-name')
            .text(logdir)
            .appendTo(running_indicator);
    };

    TensorboardList.prototype.add_reload_time = function(time, item){
        if(time == null){
            item.find(".item_modified").text(" Tensorboard Loading");
        }else{
            var reload_time = new Date();
            reload_time.setTime(time * 1000);
            item.find(".item_modified").attr("title", "Tensorboard last reload summary files time: " + reload_time.toLocaleString()).text("Last Reload:" + reload_time.toLocaleTimeString());
        }
    }

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
