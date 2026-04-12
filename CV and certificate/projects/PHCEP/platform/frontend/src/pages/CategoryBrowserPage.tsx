import React, { useEffect, useState } from 'react';
import {
  Typography, Table, Tag, Spin, Empty, Space, Button, DatePicker,
  Select, Input, Collapse, Badge, Statistic, Row, Col, Card, Tooltip, Divider,
} from 'antd';
import {
  AppstoreOutlined, CalendarOutlined, LinkOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

const ENTRY_TYPES = ['ICD10', 'SYMPTOM', 'EBM', 'LAB', 'IMAGING', 'NOTE'];
const typeColor: Record<string, string> = {
  ICD10: 'blue', SYMPTOM: 'orange', EBM: 'purple',
  LAB: 'cyan', IMAGING: 'geekblue', NOTE: 'default',
};

interface ClinicalEntry {
  id: string;
  entryType: string;
  icd10Code?: string;
  rawText: string;
  ebmStatement?: string;
  sourceUrl?: string;
  sourceName?: string;
  examDate?: string;
  inputTimestamp: string;
  geminiCategory?: string;
  geminiConfidence?: number;
  pseudonymousUserToken: string;
  tags?: string[];
}

interface DailySummary {
  date: string;
  byCategory: Record<string, number>;
  totalEbm: number;
}

const columns = [
  {
    title: 'Type',
    dataIndex: 'entryType',
    key: 'type',
    width: 90,
    render: (v: string) => <Tag color={typeColor[v] || 'default'}>{v}</Tag>,
  },
  { title: 'ICD-10', dataIndex: 'icd10Code', key: 'icd10', width: 80 },
  {
    title: 'EBM Statement / Note',
    key: 'statement',
    ellipsis: true,
    render: (_: any, r: ClinicalEntry) => (
      <Tooltip title={r.rawText}>
        <span>{r.ebmStatement || r.rawText}</span>
      </Tooltip>
    ),
  },
  {
    title: 'Source',
    key: 'source',
    width: 120,
    render: (_: any, r: ClinicalEntry) =>
      r.sourceUrl ? (
        <a href={r.sourceUrl} target="_blank" rel="noopener noreferrer">
          <LinkOutlined /> {r.sourceName || 'Link'}
        </a>
      ) : (
        r.sourceName || '-'
      ),
  },
  {
    title: 'Exam Date',
    dataIndex: 'examDate',
    key: 'examDate',
    width: 100,
    render: (v?: string) => v || '-',
  },
  {
    title: 'Input Time',
    dataIndex: 'inputTimestamp',
    key: 'ts',
    width: 130,
    render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
  },
  {
    title: 'User (de-id)',
    dataIndex: 'pseudonymousUserToken',
    key: 'user',
    width: 120,
    ellipsis: true,
    render: (v: string) => <Text code style={{ fontSize: 11 }}>{v.slice(0, 10)}…</Text>,
  },
];

const CategoryBrowserPage: React.FC = () => {
  const [entries, setEntries] = useState<ClinicalEntry[]>([]);
  const [grouped, setGrouped] = useState<Record<string, ClinicalEntry[]>>({});
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [summaryDate, setSummaryDate] = useState(dayjs());
  const [filterType, setFilterType] = useState<string | undefined>();
  const [filterIcd10, setFilterIcd10] = useState('');

  const TOKEN = 'demo-token';

  const fetchSummary = async (date: dayjs.Dayjs) => {
    try {
      const resp = await axios.get('/api/entries/summary', {
        params: { date: date.format('YYYY-MM-DD') },
      });
      setSummary(resp.data);
    } catch { /* silent */ }
  };

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { pseudonymousToken: TOKEN, size: '500' };
      if (filterType) params.entryType = filterType;
      if (filterIcd10) params.icd10Code = filterIcd10;
      const resp = await axios.get('/api/entries', { params });
      const list: ClinicalEntry[] = resp.data.content ?? resp.data;
      setEntries(list);

      // Group by gemini_category
      const g: Record<string, ClinicalEntry[]> = {};
      for (const e of list) {
        const cat = e.geminiCategory || '(Unclassified)';
        if (!g[cat]) g[cat] = [];
        g[cat].push(e);
      }
      setGrouped(g);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
    fetchSummary(summaryDate);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // Initial load only. fetchEntries is re-triggered by the Apply button;
  // fetchSummary is re-triggered by handleDateChange.

  const handleDateChange = (d: dayjs.Dayjs | null) => {
    if (d) {
      setSummaryDate(d);
      fetchSummary(d);
    }
  };

  return (
    <div>
      <Title level={3}>
        <AppstoreOutlined style={{ marginRight: 8 }} />
        Browse by Category
      </Title>
      <Paragraph type="secondary">
        Entries grouped by Gemini-inferred clinical category. Switch to the daily
        summary to see what was entered on a specific date without running the ML model.
      </Paragraph>

      {/* ── Daily Summary ──────────────────────────────────────────────────── */}
      <Card
        title={
          <Space>
            <CalendarOutlined />
            <span>Daily Digest</span>
            <DatePicker
              value={summaryDate}
              onChange={handleDateChange}
              style={{ marginLeft: 8 }}
            />
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        {summary ? (
          <>
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col>
                <Statistic title="EBM entries today" value={summary.totalEbm} />
              </Col>
              <Col>
                <Statistic
                  title="Categories seen"
                  value={Object.keys(summary.byCategory).length}
                />
              </Col>
            </Row>
            <Space wrap>
              {Object.entries(summary.byCategory).map(([cat, cnt]) => (
                <Badge key={cat} count={cnt} color="blue">
                  <Tag style={{ padding: '4px 8px' }}>{cat}</Tag>
                </Badge>
              ))}
            </Space>
          </>
        ) : (
          <Text type="secondary">No data for this date.</Text>
        )}
      </Card>

      {/* ── Filters ────────────────────────────────────────────────────────── */}
      <Divider />
      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder="Filter by type"
          style={{ width: 140 }}
          onChange={v => setFilterType(v)}
        >
          {ENTRY_TYPES.map(t => <Select.Option key={t}>{t}</Select.Option>)}
        </Select>
        <Input
          placeholder="ICD-10"
          style={{ width: 100 }}
          value={filterIcd10}
          onChange={e => setFilterIcd10(e.target.value)}
        />
        <Button type="primary" onClick={fetchEntries}>Apply</Button>
      </Space>

      {/* ── Grouped view ───────────────────────────────────────────────────── */}
      {loading ? (
        <Spin size="large" style={{ marginTop: 60, display: 'block' }} />
      ) : entries.length === 0 ? (
        <Empty description="No entries found. Add data via Daily Intake." />
      ) : (
        <Collapse accordion>
          {Object.entries(grouped)
            .sort(([, a], [, b]) => b.length - a.length)
            .map(([cat, rows]) => (
              <Panel
                key={cat}
                header={
                  <Space>
                    <Text strong>{cat}</Text>
                    <Badge count={rows.length} color="blue" />
                  </Space>
                }
              >
                <Table
                  dataSource={rows}
                  columns={columns}
                  rowKey="id"
                  size="small"
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 900 }}
                />
              </Panel>
            ))}
        </Collapse>
      )}
    </div>
  );
};

export default CategoryBrowserPage;
