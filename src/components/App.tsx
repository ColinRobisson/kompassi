import * as React from 'react';
import { Route, Switch } from 'react-router';

import FormEditorView from './FormEditorView';
import FormView from './FormView';
import FrontPage from './FrontPage';
import Navigation from './Navigation';
import NotFound from './NotFound';


class App extends React.Component {
  render() {
    return (
      <div className='Application'>
        <Navigation />
        <Switch>
          <Route exact={true} path="/" component={FrontPage} />
          <Route path="/forms/:formSlug/edit" component={FormEditorView} />
          <Route path="/forms/:formSlug" component={FormView} />
          <Route render={NotFound} />
        </Switch>
      </div>
    );
  }
}

export default App;
