import React, { useEffect, useState } from 'react';
import {
  Typography, Input, Table, Tag, Spin, Empty, Space, Button,
} from 'antd';
import { SearchOutlined, BookOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph, Text } = Typography;

interface AbbreviationMaster {
  abbreviation: string;
  expansion: string;
  icd10Context?: string;
  occurrenceCount: number;
  lastSeenAt: string;
}

const columns = [
  {
    title: 'Abbreviation',
    dataIndex: 'abbreviation',
    key: 'abbr',
    width: 140,
    render: (v: string) => <Text strong code>{v}</Text>,
    sorter: (a: AbbreviationMaster, b: AbbreviationMaster) =>
      a.abbreviation.localeCompare(b.abbreviation),
  },
  {
    title: 'Expansion',
    dataIndex: 'expansion',
    key: 'expansion',
    render: (v: string) => <Text>{v}</Text>,
  },
  {
    title: 'ICD-10 Context',
    dataIndex: 'icd10Context',
    key: 'icd10',
    width: 110,
    render: (v?: string) => v ? <Tag color="blue">{v}</Tag> : '-',
  },
  {
    title: 'Uses',
    dataIndex: 'occurrenceCount',
    key: 'count',
    width: 80,
    sorter: (a: AbbreviationMaster, b: AbbreviationMaster) =>
      a.occurrenceCount - b.occurrenceCount,
    defaultSortOrder: 'descend' as const,
    render: (v: number) => <Tag color={v > 5 ? 'green' : 'default'}>{v}</Tag>,
  },
  {
    title: 'Last Seen',
    dataIndex: 'lastSeenAt',
    key: 'lastSeen',
    width: 130,
    render: (v: string) =>
      v ? new Date(v).toLocaleDateString('en-CA') : '-',
  },
];

const AbbreviationGlossaryPage: React.FC = () => {
  const [data, setData] = useState<AbbreviationMaster[]>([]);
  const [filtered, setFiltered] = useState<AbbreviationMaster[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQ, setSearchQ] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const resp = await axios.get('/api/entries/abbreviations');
      setData(resp.data);
      setFiltered(resp.data);
    } catch {
      // silent — table shows empty state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onSearch = async () => {
    if (!searchQ.trim()) {
      setFiltered(data);
      return;
    }
    try {
      const resp = await axios.get('/api/entries/abbreviations/search', { params: { q: searchQ } });
      setFiltered(resp.data);
    } catch {
      // fallback to client-side filter
      const q = searchQ.toLowerCase();
      setFiltered(data.filter(
        r => r.abbreviation.toLowerCase().includes(q) ||
             r.expansion.toLowerCase().includes(q)
      ));
    }
  };

  const onClear = () => {
    setSearchQ('');
    setFiltered(data);
  };

  return (
    <div>
      <Title level={3}>
        <BookOutlined style={{ marginRight: 8 }} />
        Abbreviation Glossary
      </Title>
      <Paragraph type="secondary">
        Auto-synthesised from your daily clinical entries by Gemini.
        Each abbreviation is linked to the most frequent ICD-10 context it appeared in.
      </Paragraph>

      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Search abbreviation or expansion…"
          value={searchQ}
          onChange={e => setSearchQ(e.target.value)}
          onPressEnter={onSearch}
          style={{ width: 300 }}
          prefix={<SearchOutlined />}
          allowClear
          onClear={onClear}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={onSearch}>
          Search
        </Button>
        <Button onClick={load}>Refresh</Button>
      </Space>

      {loading ? (
        <Spin size="large" style={{ marginTop: 60, display: 'block' }} />
      ) : filtered.length === 0 ? (
        <Empty description="No abbreviations yet. Add clinical notes to build the glossary." />
      ) : (
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="abbreviation"
          pagination={{ pageSize: 30 }}
          size="small"
          scroll={{ x: 700 }}
        />
      )}
    </div>
  );
};

export default AbbreviationGlossaryPage;
