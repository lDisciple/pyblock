import {webSocket, WebSocketSubject} from 'rxjs/webSocket';
import {EMPTY, Subject, BehaviorSubject} from 'rxjs';
import {catchError, switchAll, tap} from 'rxjs/operators';
import {CONFIG} from '../constants';
import {SubSink} from 'subsink';

interface Message {
  type: string;
}

type VariableDefinition = { name: string, type: string, id: string, value: any };

interface StatusMessage extends Message {
  taskCount: number;
  highlights: string[];
  isRunning: boolean;
  variables: VariableDefinition[];
}

export default class CodeExecutor {
  private socket$: WebSocketSubject<any>;
  private messagesSubject$ = new Subject();
  private messages$ = new Subject();
  private subSink = new SubSink();

  public variables$ = new BehaviorSubject<{ [p: string]: any }>({});
  public isRunning$ = new BehaviorSubject(false);
  public taskCount$ = new BehaviorSubject(0);
  public highlights$ = new BehaviorSubject<string[]>([]);

  public connect(): void {
    if (!this.socket$ || this.socket$.closed) {
      this.socket$ = this.getNewWebSocket();
      this.subSink.add(
        this.socket$.subscribe({
          next: value => {
            if (!this.parseInternalMessages(value)) {
              this.messagesSubject$.next(value);
            }
          },
          error: error => {
            if (error.type === 'close') {
              this.close();
              return;
            }
            console.log(error);
          },
          complete: this.close
        })
      );
    }
  }

  public isOpen() {
    return !this.socket$.closed;
  }


  public loadProgram(program: string) {
    this.sendMessage({
      type: 'program',
      value: program
    });
  }

  public start(isEager: boolean = false) {
    this.sendMessage({
      type: 'start',
      isEager
    });
  }

  public stop() {
    this.sendMessage({
      type: 'stop'
    });
  }

  public step() {
    this.sendMessage({
      type: 'step'
    });
  }

  public status() {
    this.sendMessage({
      type: 'status'
    });
  }

  public complete() {
    this.sendMessage({
      type: 'complete'
    });
  }

  private getNewWebSocket() {
    return webSocket(CONFIG.websocketEndpoint);
  }

  /**
   * Parses internal message types
   * @return True if the message is an internal message
   */
  private parseInternalMessages(message: Message): boolean {
    switch (message.type) {
      case 'status':
        this.onStatusMessage(message as StatusMessage);
        return false;
    }
    return false;
  }

  private onStatusMessage(message: StatusMessage) {
    this.isRunning$.next(message.isRunning);
    this.taskCount$.next(message.taskCount);
    this.highlights$.next(message.highlights);
    const variables: { [k: string]: string } = {};
    for (const variableDefinition of message.variables) {
      if (!CONFIG.visibleVariables.includes(variableDefinition.type)) {
        continue;
      }
      variables[variableDefinition.name] = variableDefinition.value;
    }
    this.variables$.next(variables);
  }

  onMessage(callback: (message: any) => void) {
    this.subSink.add(this.messagesSubject$.subscribe(callback));
  }

  sendMessage(msg: any) {
    this.socket$.next(msg);
  }

  onClose(callback: () => {}) {
    this.socket$.subscribe({complete: callback});
  }

  close = () => {
    this.sendMessage({type: 'exit'});
    this.isRunning$.next(false);
    this.socket$.complete();
    this.subSink.unsubscribe();
    this.highlights$.complete();
    this.isRunning$.complete();
    this.variables$.complete();
    this.taskCount$.complete();
  }
}
