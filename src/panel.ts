import {
    Time
} from '@jupyterlab/coreutils';

import {
  Message
} from '@lumino/messaging';

import {
  Widget
} from '@lumino/widgets';

import {
    ElementExt
} from '@lumino/domutils';

import {
  DOMUtils, Dialog, showDialog
} from '@jupyterlab/apputils';

import { 
  Tensorboard 
} from './tensorboard';

import { 
  Signal, ISignal 
} from '@lumino/signaling';


/**
 * The class name added to a tensorboard widget.
 */
const TENSORBOARDS_CLASS = 'jp-Tensorboards';

const HEADER_CLASS = 'jp-Tensorboards-header';

const REFRESH_CLASS = 'jp-Tensorboards-headerRefresh';

const TENSORBOARD_CLASS = 'jp-Tensorboards-tensorboardSection';

const SHUTDOWN_TENSORBOARD_CLASS = 'jp-Tensorboards-ShutdownAll';

const SECTION_HEADER_CLASS = 'jp-Tensorboards-sectionHeader';

const CONTAINER_CLASS = 'jp-Tensorboards-sectionContainer';

const LIST_CLASS = 'jp-Tensorboards-sectionList';

const TENSORBOARD_ITEM_CLASS = 'jp-Tensorboards-item';

const TENSORBOARD_ICON_CLASS = 'jp-Tensorboards-itemIcon';

const TENSORBOARD_LABEL_CLASS = 'jp-Tensorboards-itemLabel';

const SHUTDOWN_BUTTON_CLASS = 'jp-Tensorboards-itemShutdown';

/**
 * A class that exposes the running tensorboards.
 */
export
class RunningTensorboards extends Widget {
    /**
     * Construct a new running widget.
     */
    constructor(options: RunningTensorboards.IOptions) {
        super({
            node: (options.renderer || RunningTensorboards.defaultRenderer).createNode()
        });
        let manager = this._manager = options.manager;
        this._renderer = options.renderer || RunningTensorboards.defaultRenderer;
        this.addClass(TENSORBOARDS_CLASS);

        // Populate the tensorboard section.
        let tensorboardNode = DOMUtils.findElement(this.node, TENSORBOARD_CLASS);
        let tensorboardHeader = this._renderer.createTensorboardHeaderNode();
        tensorboardHeader.className = SECTION_HEADER_CLASS;
        tensorboardNode.appendChild(tensorboardHeader);
        let tensorboardContainer = document.createElement('div');
        tensorboardContainer.className = CONTAINER_CLASS;
        let tensorboardList = document.createElement('ul');
        tensorboardList.className = LIST_CLASS;
        tensorboardContainer.appendChild(tensorboardList);
        tensorboardNode.appendChild(tensorboardContainer);
        
        manager.runningChanged.connect(this._onTensorboardsChanged, this);
    }

    /**
     * The renderer used by the tensorboard widget.
     */
    get renderer(): RunningTensorboards.IRenderer {
        return this._renderer;
    }

    get tensorboardOpenRequested(): ISignal<this, Tensorboard.IModel> {
        return this._tensorboardOpenRequested;
    }

    get tensorboardShutdownRequested(): ISignal<this, Tensorboard.IModel> {
        return this._tensorboardShutdownRequested;
    }

    /**
     * Refresh the widget.
     */
    refresh(): Promise<void> {
        clearTimeout(this._refreshId);
        let promise: Promise<void>[] = [];
        promise.push(this._manager.refreshRunning());
        return Promise.all(promise).then(() => void 0);
    }

    /**
     * Handle the DOM events for the widget.
     * 
     * @param event - The DOM event sent to the widget.
     */
    handleEvent(event: Event): void {
        if (event.type === 'click') {
            this._evtClick(event as MouseEvent);
        }
    }

    /**
     * A message handler invoked on an `'after-attach'` message.
     */
    protected onAfterAttach(msg: Message): void {
        this.node.addEventListener('click', this);
    }

    /**
     * A message handler invoked on a `'before-detach'` message.
     */
    protected onBeforeDetach(msg: Message): void {
        this.node.removeEventListener('click', this);
    }

    /**
     * A message handler invoked on an `'update-request'` message.
     */
    protected onUpdateRequest(msg: Message): void {
        let tbSection = DOMUtils.findElement(this.node, TENSORBOARD_CLASS);
        let tbList = DOMUtils.findElement(tbSection, LIST_CLASS);
        let renderer = this._renderer;

        // Remove any excess item nodes.
        while (tbList.children.length > this._runningTensorboards.length) {
            tbList.removeChild(tbList.firstChild!);
        }

        // Add any missing item nodes.
        while (tbList.children.length < this._runningTensorboards.length) {
            let node = renderer.createTensorboardNode();
            node.classList.add(TENSORBOARD_ITEM_CLASS);
            tbList.appendChild(node);
        }

        // Populate the nodes.
        for (let i = 0; i < this._runningTensorboards.length; i++) {
            let node = tbList.children[i] as HTMLLIElement;
            renderer.updateTensorboardNode(node, this._runningTensorboards[i]);
        }
    }

    /**
     * Handle the `'click'` event for the widget.
     * 
     * #### Notes
     * This listener is attached to the document node.
     */
    private _evtClick(event: MouseEvent): void {
        let tbSection = DOMUtils.findElement(this.node, TENSORBOARD_CLASS);
        let tbList = DOMUtils.findElement(tbSection, LIST_CLASS);
        let refresh = DOMUtils.findElement(this.node, REFRESH_CLASS);
        let shutdownTB = DOMUtils.findElement(this.node, SHUTDOWN_TENSORBOARD_CLASS);
        let renderer = this._renderer;
        let clientX = event.clientX;
        let clientY = event.clientY;

        // Check for a refresh
        if (ElementExt.hitTest(refresh, clientX, clientY)) {
            this.refresh();
            return;
        }

        // Check for tensorboard shutdown.
        if (ElementExt.hitTest(shutdownTB, clientX, clientY)) {
            showDialog({
                title: 'Shutdown All Tensorboards?',
                body: 'Shut down all tensorboards?',
                buttons: [
                    Dialog.cancelButton(), Dialog.warnButton({ label: 'SHUTDOWN' })
                ]
            }).then(result => {
                if (result.button.accept) {
                    this._manager.shutdownAll();
                }
            });
        }

        // Check for a tensorboard item click.
        let index = DOMUtils.hitTestNodes(tbList.children, clientX, clientY);
        if (index !== -1) {
            let node = tbList.children[index] as HTMLLIElement;
            let shutdown = renderer.getTensorboardShutdown(node);
            let model = this._runningTensorboards[index];
            if (ElementExt.hitTest(shutdown, clientX, clientY)) {
                this._manager.shutdown(model.name);
                return;
            }
            this._tensorboardOpenRequested.emit(model);
        }
    }

    /**
     * Handle a change to the running tensorboards.
     */
    private _onTensorboardsChanged(sender: Tensorboard.IManager, models: Tensorboard.IModel[]): void {
        for (let tb of this._runningTensorboards) {
            if (models.findIndex(value => value.name === tb.name ) === -1) {
                this._tensorboardShutdownRequested.emit(tb);
            }
        }
        this._runningTensorboards = models;
        this.update();
    }

    private _manager: Tensorboard.IManager;
    private _renderer: RunningTensorboards.IRenderer;
    private _runningTensorboards: Tensorboard.IModel[] = [];
    private _refreshId = -1;
    private _tensorboardOpenRequested = new Signal<this, Tensorboard.IModel>(this);
    private _tensorboardShutdownRequested = new Signal<this, Tensorboard.IModel>(this);
}

/**
 * The namespace for the `RunningTensorboards` class statics.
 */
export
namespace RunningTensorboards {
    /**
     * An options object for creating a running tensorboards widget.
     */
    export
    interface IOptions {
        /**
         * A tensorboard manager instance.
         */
        manager: Tensorboard.IManager;

        /**
         * The renderer for the running tensorboards widget.
         */
        renderer?: IRenderer;
    }
    
    /**
     * A renderer for use with a running tensorboard widget.
     */
    export
    interface IRenderer {
        /**
         * Create the root node for the running tensorboards widget.
         */
        createNode(): HTMLElement;

        /**
         * Create a node for a running tensorboard item.
         * 
         * @returns A new node for a running tensorboard item.
         */
        createTensorboardNode(): HTMLLIElement;

        /**
         * Create a fully populated header node for the tensorboards section.
         * 
         * @returns A new node for a running tensorboard header.
         */
        createTensorboardHeaderNode(): HTMLElement;

        /**
         * Get the shutdown node for a tensorboard node.
         * 
         * @param node - A node created by a call to `createTensorboardNode`.
         * 
         * @returns The node representing the shutdown option.
         */
        getTensorboardShutdown(node: HTMLLIElement): HTMLElement;

        /**
         * Populate a node with running tensorboard data.
         * 
         * @param node - A node created by a call to `createTensorboardNode`.
         * 
         * @param model - The models of tensorboard.
         * 
         * #### Notes
         * This method should completely reset the state of the node to
         * reflect the data for the tensorboard models.
         */
        updateTensorboardNode(node: HTMLLIElement, model: Tensorboard.IModel): void;
    }

    /**
     * The default implementation of `IRenderer`.
     */
    export
    class Renderer implements IRenderer {
        /**
         * Create the root node for the running tensorboard widget.
         */
        createNode(): HTMLElement {
            let node = document.createElement('div');
            let header = document.createElement('div');
            header.className = HEADER_CLASS;
            let tensorboards = document.createElement('div');
            tensorboards.className = `${TENSORBOARD_CLASS}`;

            let refreash = document.createElement('button');
            refreash.title = 'Refresh Tensorboards List';
            refreash.className = REFRESH_CLASS;
            header.appendChild(refreash);

            node.appendChild(header);
            node.appendChild(tensorboards);
            return node;
        }

        createTensorboardHeaderNode(): HTMLElement {
            let node = document.createElement('div');
            node.textContent = 'Tensorboards';

            let shutdown = document.createElement('button');
            shutdown.title = 'Shutdown All Tensorboards';
            shutdown.className = SHUTDOWN_TENSORBOARD_CLASS;
            node.appendChild(shutdown);

            return node;
        }

        createTensorboardNode(): HTMLLIElement {
            let node = document.createElement('li');
            let icon = document.createElement('span');
            icon.className = TENSORBOARD_ICON_CLASS;
            let label = document.createElement('span');
            label.className = TENSORBOARD_LABEL_CLASS;
            let shutdown = document.createElement('button');
            shutdown.className = `${SHUTDOWN_BUTTON_CLASS} jp-mod-styled`;
            shutdown.textContent = 'SHUTDOWN';

            node.appendChild(icon);
            node.appendChild(label);
            node.appendChild(shutdown);
            return node;
        }

        getTensorboardShutdown(node: HTMLElement): HTMLElement {
            return DOMUtils.findElement(node, SHUTDOWN_BUTTON_CLASS);
        }

        updateTensorboardNode(node: HTMLLIElement, model: Tensorboard.IModel): void {
            let label = DOMUtils.findElement(node, TENSORBOARD_LABEL_CLASS);
            label.textContent = `tensorboard/${model.name}`;
            let reloadData = new Date(+model.reload_time * 1000);
            let title = (
                `Logdir: ${model.logdir}\n` + 
                `Last Reload: ${Time.format(reloadData)}`
            );
            label.title = title;
        }
    }

    /**
     * The default `Renderer` instance.
     */
    export
    const defaultRenderer = new Renderer();
}