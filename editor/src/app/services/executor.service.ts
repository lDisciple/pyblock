import {Injectable} from '@angular/core';
import {webSocket, WebSocketSubject} from 'rxjs/webSocket';
import {catchError, switchAll, tap} from 'rxjs/operators';
import {EMPTY, Subject} from 'rxjs';
import {CONFIG} from '../constants';
import {HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ExecutorService {
  constructor(private http: HttpClient) {
  }

  private socket$: WebSocketSubject<any>;
  private messagesSubject$ = new Subject();
  public messages$ = this.messagesSubject$.pipe(switchAll(), catchError(e => {
    throw e;
  }));

  public connect(): void {
    if (!this.socket$ || this.socket$.closed) {
      this.socket$ = this.getNewWebSocket();
      const messages = this.socket$.pipe(
        tap({
          error: error => console.log(error),
        }), catchError(_ => EMPTY));
      this.messagesSubject$.next();
    }
  }

  public loadBlocks() {
    return this.http.get(CONFIG.blocksEndpoint);
  }

  private getNewWebSocket() {
    return webSocket(CONFIG.websocketEndpoint);
  }

  sendMessage(msg: any) {
    this.socket$.next();
  }

  close() {
    this.socket$.complete();
  }
}
