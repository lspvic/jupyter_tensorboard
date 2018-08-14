import {
  ILayoutRestorer, JupyterLab, JupyterLabPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette, InstanceTracker, IInstanceTracker, showDialog, Dialog
} from '@jupyterlab/apputils';

import {
  ILauncher
} from '@jupyterlab/launcher';

import { 
  RunningTensorboards
} from './panel';

import {
  TensorboardManager
} from './manager';

import {
  Tensorboard 
} from './tensorboard';

import {
  TensorboardTab, OpenLogdirWidget
} from './tab';

import '../style/index.css';

const TENSORBOARD_ICON_CLASS = 'jp-Tensorboard-icon';

/**
 * The command IDs used by the tensorboard plugin.
 */
namespace CommandIDs {
  export
  const createNew = 'tensorboard:create-new';

  export
  const inputDirect = 'tensorboard:choose-direct';

  export
  const open = 'tensorboard:open';

  export
  const close = 'tensorboard:close';
}

/**
 * Initialization data for the tensorboard extension.
 */
const extension: JupyterLabPlugin<IInstanceTracker<TensorboardTab>> = {
  activate,
  id: 'tensorboard',
  requires: [ILayoutRestorer, ICommandPalette],
  optional: [ILauncher],
  autoStart: true,
};

export default extension;

function activate(app: JupyterLab, restorer: ILayoutRestorer, palette: ICommandPalette, launcher: ILauncher | null): InstanceTracker<TensorboardTab> {
  let manager = new TensorboardManager();
  let running = new RunningTensorboards({manager: manager});
  running.id = 'jp-Tensorboards';
  running.title.label = 'Tensorboards';
  
  const namespace = 'tensorboard';
  const tracker = new InstanceTracker<TensorboardTab>({ namespace })

  // Let the application restorer track the running panel for restoration of
  // application state (e.g. setting the running panel as the current side bar
  // widget).
  restorer.add(running, 'Tensorboards');

  addCommands(app, manager, tracker, launcher);

  running.tensorboardOpenRequested.connect((sender, model) => {
    app.commands.execute('tensorboard:open', { tb: model });
  });

  running.tensorboardShutdownRequested.connect((sender, model) => {
    app.commands.execute('tensorboard:close', { tb: model });
  })

  palette.addItem({ command: CommandIDs.inputDirect , category: 'Tensorboard' });

  app.shell.addToLeftArea(running, {rank: 300});
  return tracker
}

/**
 * Add the commands for the tensorboard.
 */
export
function addCommands(app: JupyterLab, manager: TensorboardManager, tracker: InstanceTracker<TensorboardTab>, launcher: ILauncher | null) {
  let { commands, serviceManager } = app;

  commands.addCommand(CommandIDs.open, {
    execute: args => {
      const model = args['tb'] as Tensorboard.IModel;
      
      // Check for a running tensorboard with the given model.
      const widget = tracker.find(value => {
        return value.tensorboard && value.tensorboard.name === model.name || false;
      });
      if (widget) {
        app.shell.activateById(widget.id);
        return widget;
      } else {
        let tb = new TensorboardTab({ model });
        tracker.add(tb);
        app.shell.addToMainArea(tb);
        app.shell.activateById(tb.id);
        return tb;
      }
    }
  });

  commands.addCommand(CommandIDs.close, {
    execute: args => {
      const model = args['tb'] as Tensorboard.IModel;

      const widget = tracker.find(value => {
        return value.tensorboard && value.tensorboard.name === model.name || false;
      });
      if (widget) {
        widget.dispose();
        widget.close();
      }
    }
  });

  commands.addCommand(CommandIDs.inputDirect, {
    label: () => 'Create a new tensorboard',
    execute: args => {
      showDialog({
        title: 'Input the logdir Path to create a new Tensorboard',
        body: new OpenLogdirWidget(),
        buttons: [Dialog.cancelButton(), Dialog.okButton({ label : 'CREATE'})],
        focusNodeSelector: 'inpute'
      }).then(result => {
        if (result.button.label === 'CREATE') {
          const logdir = <string>result.value;
          return app.commands.execute(CommandIDs.createNew, {logdir: logdir});
        } else {
          return;
        }
      });
    }
  });

  commands.addCommand(CommandIDs.createNew, {
    execute: args => {
      const logdir =  args['logdir'] as string
      return serviceManager.contents.get(logdir, { type: 'directory'}).then(dir => {
          return manager.startNew(dir.path).then(tb => {
            return app.commands.execute(CommandIDs.open, { tb: tb.model});
          });
        }, () => {
          // no such directory.
          return showDialog({
            title: 'Cannot create tensorboard.',
            body: 'Directory not found',
            buttons: [Dialog.okButton()]
          });
        });
    },
  });

  const createNew = (cwd: string) => {
      return commands.execute(CommandIDs.createNew, { logdir: cwd }).then(widget => {
          return widget;
      });
  };

  if (launcher) {
      launcher.add({
          displayName: 'Tensorboard',
          category: 'Other',
          rank: 0,
          iconClass: TENSORBOARD_ICON_CLASS,
          callback: createNew
      });
  }
}
