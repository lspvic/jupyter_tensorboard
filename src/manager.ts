//Tensorboard manager

import { 
  IIterator, ArrayExt, iter
} from '@lumino/algorithm';

import {
    Signal, ISignal
} from '@lumino/signaling';

import {
  JSONExt
} from '@lumino/coreutils';

import { 
  Tensorboard
} from './tensorboard';

import {
    ServerConnection
} from '@jupyterlab/services';

/**
 * A tensorboard manager.
 */
export
class TensorboardManager implements Tensorboard.IManager {
    /**
     * Construct a new tensorboard manager.
     */
    constructor(options: TensorboardManager.IOptions = {}) {
        this.serverSettings = options.serverSettings || ServerConnection.makeSettings();
        this._readyPromise = this._refreshRunning();
        this._refreshTimer = (setInterval as any)(() => {
            if (typeof document !== 'undefined' && document.hidden) {
                return;
            }
            this._refreshRunning();
        }, 10000);
    }

    /**
     * A signal emitted when the running tensorboards change.
     */
    get runningChanged(): ISignal<this, Tensorboard.IModel[]> {
        return this._runningChanged;
    }

    /**
     * Test whether the terminal manager is disposed.
     */
    get isDisposed(): boolean {
        return this._isDisposed;
    }

    /**
     * The server settings of the manager.
     */
    readonly serverSettings: ServerConnection.ISettings;

    /**
     * Dispose of the resources used by the manager.
     */
    dispose(): void {
        if (this.isDisposed) {
            return;
        }
        this._isDisposed = true;
        clearInterval(this._refreshTimer);
        Signal.clearData(this);
        this._models = [];
    }
    
    /**
     * Test whether the manager is ready.
     */
    get isReady(): boolean {
        return this._isReady;
    }

    /**
     * A promise that fulfills when the manager is ready.
     */
    get ready(): Promise<void> {
        return this._readyPromise;
    }

    /**
     * Create an iterator over the most recent running Tensorboards.
     * 
     * @returns A new iterator over the running tensorboards.
     */
    running(): IIterator<Tensorboard.IModel> {
        return iter(this._models);
    }

    /**
     * Create a new tensorboard.
     * 
     * @param logdir - The logdir used to create a new tensorboard.
     * 
     * @param options - The options used to connect to the tensorboard.
     * 
     * @returns A promise that resolves with the tensorboard instance.
     */
    startNew(logdir: string, options?: Tensorboard.IOptions): Promise<Tensorboard.ITensorboard> {
        return Tensorboard.startNew(logdir, this._getOptions(options)).then(tensorboard => {
            this._onStarted(tensorboard);
            return tensorboard;
        }); 
    }

    /** 
     * Shut down a tensorboard by name.
    */
    shutdown(name: string): Promise<void> {
        let index = ArrayExt.findFirstIndex(this._models, value => value.name === name);
        if (index === -1) {
            return;
        }

        this._models.splice(index, 1);
        this._runningChanged.emit(this._models.slice());

        return Tensorboard.shutdown(name, this.serverSettings).then(() => {
            let toRemove: Tensorboard.ITensorboard[] = [];
            this._tensorboards.forEach(t => {
                if (t.name === name) {
                    t.dispose();
                    toRemove.push(t);
                }
            });
            toRemove.forEach(s => {this._tensorboards.delete(s); });
        });
    }

    /**
     * Shut down all tensorboards.
     * 
     * @returns A promise that resolves when all of the tensorboards are shut down.
     */
    shutdownAll(): Promise<void> {
        let models = this._models;
        if (models.length > 0) {
            this._models = [];
            this._runningChanged.emit([]);
        }

        return this._refreshRunning().then(() => {
            return Promise.all(models.map(model => {
                return Tensorboard.shutdown(model.name, this.serverSettings).then(() => {
                    let toRemove: Tensorboard.ITensorboard[] = [];
                    this._tensorboards.forEach(t => {
                        t.dispose();
                        toRemove.push(t);
                    });
                    toRemove.forEach(t => {this._tensorboards.delete(t); });
                });
            })).then(() => {return undefined; });
        });
    }

    /**
     * Force a refresh of the running tensorboards.
     * 
     * @returns A promise that with the list of running tensorboards.
     */
    refreshRunning(): Promise<void> {
        return this._refreshRunning();
    }

    /**
     * Handle a tensorboard terminating.
     */
    private _onTerminated(name: string): void {
        let index = ArrayExt.findFirstIndex(this._models, value => value.name === name);
        if (index !== -1) {
            this._models.splice(index, 1);
            this._runningChanged.emit(this._models.slice());
        }
    }

    /**
     * Handle a tensorboard starting.
     */
    private _onStarted(tensorboard: Tensorboard.ITensorboard): void {
        let name = tensorboard.name;
        this._tensorboards.add(tensorboard);
        let index = ArrayExt.findFirstIndex(this._models, value => value.name === name);
        if (index === -1) {
            this._models.push(tensorboard.model);
            this._runningChanged.emit(this._models.slice());
        }
        tensorboard.terminated.connect(() => {
            this._onTerminated(name);
        });
    }

    /**
     * Refresh the running tensorboards.
     */
    private _refreshRunning(): Promise<void> {
        return Tensorboard.listRunning(this.serverSettings).then(models => {
            this._isReady = true;
            if (!JSONExt.deepEqual(models, this._models)) {
                let names = models.map(r => r.name);
                let toRemove: Tensorboard.ITensorboard[] = [];
                this._tensorboards.forEach(t => {
                    if (names.indexOf(t.name) === -1) {
                        t.dispose();
                        toRemove.push(t);
                    }
                });
                toRemove.forEach(t => {this._tensorboards.delete(t); });
                this._models = models.slice();
                this._runningChanged.emit(models);
            }
        });
    }

    /**
     * Get a set of options to pass.
     */
    private _getOptions(options: Tensorboard.IOptions = {}): Tensorboard.IOptions  {
        return { ...options, serverSettings: this.serverSettings };
    }

    private _models: Tensorboard.IModel[] = [];
    private _tensorboards = new Set<Tensorboard.ITensorboard>();
    private _isDisposed = false;
    private _isReady = false;
    private _readyPromise: Promise<void>;
    private _refreshTimer = -1;
    private _runningChanged = new Signal<this, Tensorboard.IModel[]>(this);
} 
/**
 * The namespace for TensorboardManager statics.
 */
export
namespace TensorboardManager{
    /**
     * The options used to initialize a tensorboard manager.
     */
    export
    interface IOptions {
        /**
         * The server settings used by the manager.
         */
        serverSettings?: ServerConnection.ISettings;
    }
}