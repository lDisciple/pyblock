import {Component, CUSTOM_ELEMENTS_SCHEMA, ElementRef, HostListener, NO_ERRORS_SCHEMA, OnDestroy, OnInit, ViewChild} from '@angular/core';

import * as Blockly from 'scratch-blocks';
import {HttpClient, provideHttpClient} from '@angular/common/http';
import CodeExecutor from './models/code-executor.model';
import {CONFIG} from './constants';
import {tap} from 'rxjs/operators';
import {NgxJsonViewerModule} from 'ngx-json-viewer';
import {AsyncPipe, NgIf} from '@angular/common';
import {SubSink} from 'subsink';
import {Subscription} from 'rxjs';
import {FormsModule} from '@angular/forms';
import {Title} from '@angular/platform-browser';
import { Location } from '@angular/common';

@Component({
  standalone: true,
  selector: 'pyblock-editor',
  templateUrl: './pyblock.component.html',
  styleUrls: ['./pyblock.component.css'],
  imports: [
    NgxJsonViewerModule,
    AsyncPipe,
    NgIf,
    FormsModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA]
})
export class PyblockComponent implements OnInit, OnDestroy {
  toolboxUrl: string;
  workspace: any;
  output = 'Disconnected';
  executor: CodeExecutor;
  subSink = new SubSink();
  highlightListener: Subscription;
  highlights = [];
  statusIntervalId: number;
  name: string = null;

  @ViewChild('outputArea', {static: true, read: ElementRef})
  outputElement: ElementRef;

  constructor(private http: HttpClient, private titleService: Title, location: Location) {
    this.toolboxUrl = 'assets/toolbox.xml';
    this.statusIntervalId = setInterval(() => {
      if (this.executor) {
        this.executor.status();
      }
    }, 1000);
  }

  ngOnInit() {
    this.loadBlocks().subscribe(
      () =>
        this.http.get(this.toolboxUrl, {
          responseType: 'text'
        }).subscribe(res => {
          const toolboxElement = document.createElement('div');
          toolboxElement.innerHTML = res;
          this.initBlockly(toolboxElement.firstChild);
        })
    );
  }

  @HostListener('document:keydown.control.s', ['$event']) onKeydownHandler(event: KeyboardEvent) {
    event.preventDefault();
    this.onSave();
  }

  loadBlocks() {
    return this.http.get<{ k: string }>(CONFIG.blocksEndpoint)
      .pipe(
        tap(blocks => {
          console.log(blocks);
          for (const key of Object.keys(blocks)) {
            // noinspection JSUnusedGlobalSymbols
            Blockly.Blocks[key] = {
              init() {
                this.jsonInit(blocks[key]);
              }
            };
          }
        })
      );
  }

  initBlockly(toolbox: Node) {
    this.workspace = Blockly.inject('blocklyDiv', {
      comments: true,
      disable: false,
      collapse: false,
      media: '../media/',
      readOnly: false,
      rtl: false,
      scrollbars: true,
      toolbox,
      toolboxPosition: 'start',
      horizontalLayout: false,
      sounds: false,
      zoom: {
        controls: true,
        wheel: true,
        startScale: 0.675,
        maxScale: 4,
        minScale: 0.25,
        scaleSpeed: 1.1
      },
      colours: {
        fieldShadow: 'rgba(255, 255, 255, 0.3)',
        dragShadowOpacity: 0.6
      }
    });

    this.onLoad();
    this.updatePageTitle();
  }

  onSave() {
    const exportedXml = Blockly.Xml.workspaceToDom(this.workspace);
    localStorage.setItem('lastSave', Blockly.Xml.domToPrettyText(exportedXml));
    localStorage.setItem('name', this.name);
    console.log(exportedXml);
  }

  onLoad() {
    const text = localStorage.getItem('lastSave');
    this.name = localStorage.getItem('name');
    const xml = Blockly.Xml.textToDom(text);
    Blockly.Xml.domToWorkspace(xml, this.workspace);
    this.updatePageTitle();
    console.log(xml);
  }

  private loadNewExecutor() {
    if (this.executor) {
      this.executor.close();
      this.highlightListener.unsubscribe();
    }
    this.clearLog();
    this.executor = new CodeExecutor();
    this.executor.connect();
    const programXml = Blockly.Xml.workspaceToDom(this.workspace);
    this.log('Connected');

    this.highlightBlocks([]);
    this.highlightListener = this.executor.highlights$.subscribe({
      next: blockIds => this.highlightBlocks(blockIds)
    });
    this.executor.onMessage((message: any) => {
      if (message.type === 'log') {
        console.log(message.value);
      }
      if (message.type === 'status') {
        const broadcastList: [string, string][] = message.broadcasts;
        if (broadcastList) {
          for (const item of broadcastList) {
            this.log(`[broadcast] ${item[0]}: ${item[1]}`);
          }
        }
      }
      if (message.type === 'error') {
        this.log(`[Error] ${message.value}`);
      }
      console.log(message);
    });
    this.executor.onClose(() => this.executor = null);
    this.executor.loadProgram(Blockly.Xml.domToText(programXml));
    return this.executor;
  }

  private highlightBlocks(blockIds: string[]) {
    // this.workspace.glowBlock(null);
    for (const id of this.highlights) {
      this.workspace.glowBlock(id, false);
      this.workspace.glowStack(id, false);
    }
    for (const id of blockIds) {
      this.workspace.glowBlock(id, true);
      this.workspace.glowStack(id, true);
      this.highlights.push(id);
    }
  }

  onRun() {
    const executor = this.loadNewExecutor();
    executor.start(true);
    executor.complete();
  }

  onDebug() {
    const executor = this.loadNewExecutor();
    executor.start();
  }

  onStep() {
    if (!this.executor) {
      return;
    }
    this.executor.step();
  }

  onStop() {
    if (this.executor?.isOpen()) {
      this.executor.close();
      this.log('Disconnected');
    }
  }

  onFinish() {
    if (!this.executor) {
      return;
    }
    this.executor.complete();
  }

  log = (text: string) => {
    if (this.output) {
      this.output = this.output + '\n';
    }
    this.output = this.output + text;
  };

  ngOnDestroy() {
    this.highlightListener.unsubscribe();
    this.subSink.unsubscribe();
    clearInterval(this.statusIntervalId);
  }

  private clearLog() {
    this.output = '';
  }

  onImport(fileEvent) {
    const file: File = fileEvent.target.files[0];
    if (file) {
      const fileName = file.name;
      const reader = new FileReader();
      reader.onload = event => {
        const xmlText = event.target.result;
        const dom = Blockly.Xml.textToDom(xmlText);
        Blockly.Xml.clearWorkspaceAndLoadFromXml(dom, this.workspace);
        this.name = fileName.replace(/\.xml$/, '');
        this.updatePageTitle();

      }; // desired file content
      reader.onerror = error => console.error(error);
      reader.readAsText(file);
    }
  }

  onExport() {
    const programXml = Blockly.Xml.workspaceToDom(this.workspace);
    const element = document.createElement('a');
    const blob = new Blob([Blockly.Xml.domToText(programXml)], {type: 'text/xml'});
    const url = URL.createObjectURL(blob);
    element.href = url;
    const projectName = this.name ?? 'untitled-pyblock';
    element.setAttribute('download', `${projectName}.xml`);
    document.body.appendChild(element);
    element.click();
  }

  private updatePageTitle() {
    if (this.name) {
      this.titleService.setTitle(`PyBlock - ${this.name}`);
    } else {
      this.titleService.setTitle(`PyBlock`);
    }
  }
}
