import React from 'react';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import Home from './Home';
import DataLineage from './DataLineage';
import './App.css';

function App() {
    return (
        <Router>
            <div className="App">
                <header className="app-header">
                    <Link to="/" className="logo">
                        <i className="fas fa-project-diagram"></i>
                        <span>Data Lineage App</span>
                    </Link>
                </header>
                <main className="app-content">
                    <Switch>
                        <Route path="/" exact component={Home} />
                        <Route path="/file/:id" component={DataLineage} />
                    </Switch>
                </main>
            </div>
        </Router>
    );
}

export default App;
