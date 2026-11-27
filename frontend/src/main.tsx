import {Component,type ErrorInfo,type ReactNode} from 'react';
import {createRoot} from 'react-dom/client';
import {App} from './app/App';
import './styles/tokens.css';
import './styles/app.css';

class Boundary extends Component<{children:ReactNode},{failed:boolean}>{
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  componentDidCatch(_error:Error,_info:ErrorInfo){/* Private state never goes to diagnostic logs. */}
  render(){return this.state.failed?<div className="disconnected"><h1>Presentation unavailable</h1><p>Use native tray Stop/mute, then restart with --legacy if needed.</p></div>:this.props.children;}
}
createRoot(document.getElementById('root')!).render(<Boundary><App/></Boundary>);
