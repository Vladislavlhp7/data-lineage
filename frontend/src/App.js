import React from 'react';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import Home from './Home';
import DataLineage from './DataLineage';
import TransactionLineage from './TransactionLineage';
import BCBS239Report from './BCBS239Report';
import RiskDetailPage from './RiskDetailPage';
import RiskLineagePage from './RiskLineagePage';
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
                    <nav className="main-nav">
                        <Link to="/" className="nav-item">Home</Link>
                        <Link to="/transaction" className="nav-item">Transaction Demo</Link>
                        <Link to="/risk-lineage" className="nav-item">Risk Lineage</Link>
                        <Link to="/bcbs-report" className="nav-item">BCBS 239</Link>
                    </nav>
                </header>
                <main className="app-content">
                    <Switch>
                        <Route path="/" exact component={Home} />
                        <Route path="/file/:id" component={DataLineage} />
                        <Route path="/transaction" component={TransactionLineage} />
                        <Route path="/bcbs-report" component={BCBS239Report} />
                        <Route path="/risk-detail/:id" component={RiskDetailPage} />
                        <Route path="/risk-lineage" component={RiskLineagePage} />
                    </Switch>
                </main>
            </div>
        </Router>
    );
}

export default App;
