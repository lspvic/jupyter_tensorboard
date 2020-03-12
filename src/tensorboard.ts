
import { 
  each, map, toArray, IIterator
} from '@lumino/algorithm';

import {
  IDisposable
} from '@lumino/disposable';

import {
  JSONObject
} from '@lumino/coreutils';

import {
  URLExt
} from '@jupyterlab/coreutils';

import {
    Signal, ISignal
} from '@lumino/signaling';

import {
    ServerConnection
} from '@jupyterlab/services';

/**
 * The url for the tensorboard service. tensorboard 
 * service provided by jupyter_tensorboard.
 * ref: https://github.com/lspvic/jupyter_tensorboard
 * Maybe rewrite the jupyter_tensorboard service by myself.
 */
const TENSORBOARD_SERVICE_URL = 'api/tensorboard';

const TENSORBOARD_URL = 'tensorboard';

/**
 * The namespace for Tensorboard statics.
 */
export
namespace Tensorboard {
    /**
     * An interface for a tensorboard.
     */
    export
    interface ITensorboard extends IDisposable {
        /**
         * A signal emitted when the tensorboard is shut down.
         */
        terminated: ISignal<ITensorboard, void>;

        /**
         * The model associated with the tensorboard.
         */
        readonly model: IModel;

        /**
         * Get the name of the tensorboard.
         */
        readonly name: string;

        /**
         * The server settings for the tensorboard.
         */
        readonly serverSettings: ServerConnection.ISettings;

        /**
         * Shut down the tensorboard.
         */
        shutdown(): Promise<void>;
    }

    /**
     * Start a new tensorboard.
     * 
     * @param options - The tensorboard options to use.
     * 
     * @returns A promise that resolves with the tensorboard instance.
     */
    export
    function startNew(logdir: string, options?: IOptions): Promise<ITensorboard> {
        return DefaultTensorboard.startNew(logdir, options);
    }

    /**
     * List the running tensorboards.
     * 
     * @param settings - The server settings to use.
     * 
     * @returns A promise that resolves with the list of running tensorboard models.
     */
    export
    function listRunning(settings?: ServerConnection.ISettings): Promise<IModel[]> {
        return DefaultTensorboard.listRunning(settings);
    }

    /**
     * Shut down a tensorboard by name.
     * 
     * @param name - The name of the target tensorboard.
     * 
     * @param settings - The server settings to use.
     * 
     * @returns A promise that resolves when the tensorboard is shut down.
     */
    export
    function shutdown(name: string, settings?: ServerConnection.ISettings): Promise<void> {
        return DefaultTensorboard.shutdown(name, settings);
    }

    /**
     * Shut down all tensorboard.
     * 
     * @returns A promise that resolves when all of the tensorboards are shut down.
     */
    export
    function shutdownAll(settings?: ServerConnection.ISettings): Promise<void> {
        return DefaultTensorboard.shutdownAll(settings);
    }

    /**
     * Get tensorboard's url
     */
    export
    function getUrl(name: string, settings?: ServerConnection.ISettings): string {
        return DefaultTensorboard.getUrl(name, settings);
    }

    /**
     * The options for intializing a tensorboard object.
     */
    export
    interface IOptions{
        /**
         * The server settings for the tensorboard.
         */
        serverSettings?: ServerConnection.ISettings;
    }

    /**
     * The server model for a tensorboard.
     */
    export
    interface IModel extends JSONObject {
        /**
         * The name of the tensorboard.
         */
        readonly name: string;

        /**
         * The logdir Path of the tensorboard.
         */
        readonly logdir: string;

        /**
         * The last reload time of the tensorboard.
         */
        readonly reload_time: string;
    }

     /**
     * The interface for a tensorboard manager.
     * 
     * The manager is respoonsible for maintaining the state of running
     * tensorboard.
     */
    export
    interface IManager extends IDisposable {

        readonly serverSettings: ServerConnection.ISettings;

        runningChanged: ISignal<this, IModel[]>;

        running(): IIterator<IModel>;

        startNew(logdir: string, options?: IOptions): Promise<ITensorboard>;

        shutdown(name: string): Promise<void>;

        shutdownAll(): Promise<void>;

        refreshRunning(): Promise<void>;
    }

}

export
class DefaultTensorboard implements Tensorboard.ITensorboard {
    /**
     * Construct a new tensorboard.
     */
    constructor(name: string, logdir: string, lastReload: string, options: Tensorboard.IOptions = {}) {
        this._name = name;
        this._logdir = logdir;
        this._lastReload = lastReload;
        this.serverSettings = options.serverSettings || ServerConnection.makeSettings();
        this._url = Private.getTensorboardInstanceUrl(this.serverSettings.baseUrl, this._name);
    }

    /**
     * Get the name of the tensorboard.
     */
    get name(): string {
        return this._name;
    }

    /**
     * Get the model for the tensorboard.
     */
    get model(): Tensorboard.IModel {
        return { name: this._name, logdir: this._logdir, reload_time: this._lastReload };
    }

    /**
     * A signal emitted when the tensorboard is shut down.
     */
    get terminated(): Signal<this, void> {
        return this._terminated;
    }

    /**
     * Test whether the tensorbaord is disposed.
     */
    get isDisposed(): boolean {
        return this._isDisposed;
    }

    /**
     * Dispose of the resources held by the tensorboard.
     */
    dispose(): void {
        if (this._isDisposed) {
            return;
        }

        this.terminated.emit(void 0);
        this._isDisposed = true;
        delete Private.running[this._url];
        Signal.clearData(this);
    }

    /**
     * The server settings for the tensorboard.
     */
    readonly serverSettings: ServerConnection.ISettings;

    /**
     * Shut down the tensorboard.
     */
    shutdown(): Promise<void> {
        const {name, serverSettings } = this;
        return DefaultTensorboard.shutdown(name, serverSettings);
    }

    private _isDisposed = false;
    private _url: string;
    private _name: string;
    private _logdir: string;
    private _lastReload: string;
    private _terminated = new Signal<this, void>(this);
}


/**
 * The static namespace for `DefaultTensorboard`.
 */
export
namespace DefaultTensorboard {
    /**
     * Start a new tensorboard.
     * 
     * @param options - The tensorboard options to use.
     * 
     * @returns A promise that resolves with the tensorboard instance.
     */
    export
    function startNew(logdir: string, options: Tensorboard.IOptions = {}): Promise<Tensorboard.ITensorboard> {
        let serverSettings = options.serverSettings || ServerConnection.makeSettings();
        let url = Private.getServiceUrl(serverSettings.baseUrl);
        // ServerConnection won't automaticy add this header when the body in not none.
        let header = new Headers({ 'Content-Type': 'application/json' });
        
        let data = JSON.stringify({'logdir': logdir});

        let init = { method: 'POST' , headers: header, body: data };

        return ServerConnection.makeRequest(url, init, serverSettings).then(response => {
            if (response.status !== 200) {
                throw new ServerConnection.ResponseError(response);
            }
            return response.json();
        }).then((data: Tensorboard.IModel) => {
            let name = data.name;
            let logdir = data.logdir;
            let lastReload = data.reload_time;
            return new DefaultTensorboard(name, logdir, lastReload, {...options, serverSettings });
        });
    }
    
    /**
     * List the running tensorboards.
     * 
     * @param settings - The server settings to use.
     * 
     * @returns A promise that resolves with the list of running tensorboard models.
     */
    export
    function listRunning(settings?: ServerConnection.ISettings): Promise<Tensorboard.IModel[]> {
        settings = settings || ServerConnection.makeSettings();
        let service_url = Private.getServiceUrl(settings.baseUrl);
        let instance_url = Private.getTensorboardInstanceRootUrl(settings.baseUrl);
        return ServerConnection.makeRequest(service_url, {}, settings).then(response => {
            if (response.status !== 200) {
                throw new ServerConnection.ResponseError(response);
            }
            return response.json();
        }).then((data: Tensorboard.IModel[]) => {
            if (!Array.isArray(data)) {
                throw new Error('Invalid tensorboard data');
            }
            // Update the local data store.
            let urls = toArray(map(data, item => {
                return URLExt.join(instance_url, item.name);
            }));
            each(Object.keys(Private.running), runningUrl => {
                if (urls.indexOf(runningUrl) === -1) {
                    let tensorboard = Private.running[runningUrl];
                    tensorboard.dispose();
                }
            });
            return data;
        });
    }

    /**
     * Shut down a tensorboard by name.
     * 
     * @param name - Then name of the target tensorboard.
     * 
     * @param settings - The server settings to use.
     * 
     * @returns A promise that resolves when the tensorboard is shut down.
     */
    export
    function shutdown(name: string, settings?: ServerConnection.ISettings): Promise<void> {
        settings = settings || ServerConnection.makeSettings();
        let url = Private.getTensorboardUrl(settings.baseUrl, name);
        let init = { method: 'DELETE' };
        return ServerConnection.makeRequest(url, init, settings).then(response => {
            if (response.status === 404) {
                return response.json().then(data => {
                    console.warn(data['message']);
                    Private.killTensorboard(url);
                });
            }
            if (response.status !== 204) {
                throw new ServerConnection.ResponseError(response);
            }
            Private.killTensorboard(url);
        });
    }

    /**
     * Shut down all tensorboards.
     * 
     * @param settings - The server settings to use.
     * 
     * @returns A promise that resolves when all the tensorboards are shut down.
     */
    export
    function shutdownAll(settings?: ServerConnection.ISettings): Promise<void> {
        settings = settings || ServerConnection.makeSettings();
        return listRunning(settings).then(running => {
            each(running, s => {
                shutdown(s.name, settings);
            });
        });
    }

    /**
     * According tensorboard's name to get tensorboard's url.
     */
    export
    function getUrl(name: string, settings?: ServerConnection.ISettings): string {
        settings = settings || ServerConnection.makeSettings();
        return Private.getTensorboardInstanceUrl(settings.baseUrl, name);
    }
}


/**
 * A namespace for private data.
 */
namespace Private {
    /**
     * A mapping of running tensorboards by url.
     */
    export
    const running: { [key: string]: DefaultTensorboard } = Object.create(null);

    /**
     * Get the url for a tensorboard.  
     */
    export
    function getTensorboardUrl(baseUrl: string, name: string): string {
        return URLExt.join(baseUrl, TENSORBOARD_SERVICE_URL, name);
    }

    /**
     * Get the base url.
     */
    export
    function getServiceUrl(baseUrl: string): string {
        return URLExt.join(baseUrl, TENSORBOARD_SERVICE_URL);
    }

    /**
     * Kill tensorboard by url.
     */
    export
    function killTensorboard(url: string): void {
        // Update the local data store.
        if (Private.running[url]) {
            let tensorboard = Private.running[url];
            tensorboard.dispose();
        }
    }

    export
    function getTensorboardInstanceRootUrl(baseUrl: string): string {
        return URLExt.join(baseUrl, TENSORBOARD_URL);
    }

    export
    function getTensorboardInstanceUrl(baseUrl: string, name: string): string {
        return URLExt.join(baseUrl, TENSORBOARD_URL, name);
    }
}