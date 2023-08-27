import {enableProdMode} from '@angular/core';

import {environment} from './environments/environment';
import {bootstrapApplication} from '@angular/platform-browser';
import {PyblockComponent} from './app/pyblock.component';
import {provideHttpClient} from '@angular/common/http';

if (environment.production) {
  enableProdMode();
}

bootstrapApplication(PyblockComponent, {
  providers: [
    provideHttpClient()
  ]
}).catch(err => console.error(err));
