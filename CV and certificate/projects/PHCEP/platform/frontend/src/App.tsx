import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  QuestionCircleOutlined,
  FileTextOutlined,
  LineChartOutlined,
  BookOutlined,
  AuditOutlined,
  EditOutlined,
  ReadOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import QueryPage from './pages/QueryPage';
import ObservationsPage from './pages/ObservationsPage';
import TimelinePage from './pages/TimelinePage';
import EbmPage from './pages/EbmPage';
import AdminPage from './pages/AdminPage';
import DailyIntakePage from './pages/DailyIntakePage';
import AbbreviationGlossaryPage from './pages/AbbreviationGlossaryPage';
import CategoryBrowserPage from './pages/CategoryBrowserPage';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: 'query', icon: <QuestionCircleOutlined />, label: <Link to="/">Submit Query</Link> },
  { key: 'observations', icon: <FileTextOutlined />, label: <Link to="/observations">Health Records</Link> },
  { key: 'timeline', icon: <LineChartOutlined />, label: <Link to="/timeline">Timeline</Link> },
  { key: 'ebm', icon: <BookOutlined />, label: <Link to="/ebm">EBM Knowledge Base</Link> },
  { key: 'admin', icon: <AuditOutlined />, label: <Link to="/admin">Platform Manager</Link> },
  // ── Workflow A ──────────────────────────────────────────────────────────────
  { type: 'divider' as const },
  { key: 'intake', icon: <EditOutlined />, label: <Link to="/intake">Daily Intake</Link> },
  { key: 'glossary', icon: <ReadOutlined />, label: <Link to="/glossary">Abbreviation Glossary</Link> },
  { key: 'categories', icon: <AppstoreOutlined />, label: <Link to="/categories">Browse by Category</Link> },
];

const App: React.FC = () => (
  <Layout style={{ minHeight: '100vh' }}>
    <Sider width={220} theme="light">
      <div style={{ padding: '16px', fontWeight: 'bold', fontSize: 16, borderBottom: '1px solid #f0f0f0' }}>
        🏥 PHCEP
      </div>
      <Menu mode="inline" defaultSelectedKeys={['query']} items={menuItems} />
    </Sider>
    <Layout>
      <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
        <span style={{ fontSize: 18, fontWeight: 600 }}>Personal Health Care Evidence-Based Medicine Platform</span>
      </Header>
      <Content style={{ margin: 24, background: '#fff', padding: 24, borderRadius: 8 }}>
        <Routes>
          <Route path="/" element={<QueryPage />} />
          <Route path="/observations" element={<ObservationsPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/ebm" element={<EbmPage />} />
          <Route path="/admin" element={<AdminPage />} />
          {/* Workflow A */}
          <Route path="/intake" element={<DailyIntakePage />} />
          <Route path="/glossary" element={<AbbreviationGlossaryPage />} />
          <Route path="/categories" element={<CategoryBrowserPage />} />
        </Routes>
      </Content>
    </Layout>
  </Layout>
);

export default App;
