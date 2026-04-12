import React, { useState } from 'react';
import {
  Form, Input, Select, Button, DatePicker, Table, Typography, Space,
  message, Tag, Divider, Badge, Card, Tooltip,
} from 'antd';
import {
  PlusOutlined, SearchOutlined, FileTextOutlined, ExperimentOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const ENTRY_TYPES = ['ICD10', 'SYMPTOM', 'EBM', 'LAB', 'IMAGING', 'NOTE'];

const typeColor: Record<string, string> = {
  ICD10: 'blue',
  SYMPTOM: 'orange',
  EBM: 'purple',
  LAB: 'cyan',
  IMAGING: 'geekblue',
  NOTE: 'default',
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
  tags?: string[];
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
    title: 'Note',
    dataIndex: 'rawText',
    key: 'text',
    ellipsis: true,
    render: (v: string, r: ClinicalEntry) => (
      <Tooltip title={r.ebmStatement ? `EBM: ${r.ebmStatement}` : v}>
        <span>{v}</span>
      </Tooltip>
    ),
  },
  {
    title: 'Category',
    dataIndex: 'geminiCategory',
    key: 'category',
    width: 160,
    render: (v?: string, r?: ClinicalEntry) =>
      v ? (
        <Badge
          color="green"
          text={
            <Tooltip title={`Confidence: ${((r?.geminiConfidence ?? 0) * 100).toFixed(0)}%`}>
              <span style={{ fontSize: 12 }}>{v}</span>
            </Tooltip>
          }
        />
      ) : (
        <Text type="secondary" style={{ fontSize: 12 }}>Pending…</Text>
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
    width: 140,
    render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
  },
  {
    title: 'Source',
    key: 'source',
    width: 100,
    render: (_: any, r: ClinicalEntry) =>
      r.sourceUrl ? (
        <a href={r.sourceUrl} target="_blank" rel="noopener noreferrer">
          {r.sourceName || 'Link'}
        </a>
      ) : (
        r.sourceName || '-'
      ),
  },
];

const DailyIntakePage: React.FC = () => {
  const [form] = Form.useForm();
  const [entries, setEntries] = useState<ClinicalEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // For the Browse panel
  const [filterType, setFilterType] = useState<string | undefined>();
  const [filterIcd10, setFilterIcd10] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const TOKEN = 'demo-token'; // In production this comes from auth context

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { pseudonymousToken: TOKEN };
      if (filterType) params.entryType = filterType;
      if (filterIcd10) params.icd10Code = filterIcd10;
      if (filterCategory) params.geminiCategory = filterCategory;
      const resp = await axios.get('/api/entries', { params });
      setEntries(resp.data.content ?? resp.data);
    } catch {
      message.error('Failed to load entries');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { fetchEntries(); }, []);

  const onAdd = async (values: any) => {
    setSubmitting(true);
    try {
      await axios.post('/api/entries', {
        pseudonymousUserToken: TOKEN,
        entryType: values.entryType,
        icd10Code: values.icd10Code,
        rawText: values.rawText,
        ebmStatement: values.ebmStatement,
        sourceUrl: values.sourceUrl,
        sourceName: values.sourceName,
        examDate: values.examDate?.format('YYYY-MM-DD'),
        tags: values.tags ? values.tags.split(',').map((t: string) => t.trim()) : [],
      });
      message.success('Entry saved — Gemini classification running in the background');
      form.resetFields();
      fetchEntries();
    } catch {
      message.error('Failed to save entry');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Title level={3}>
        <FileTextOutlined style={{ marginRight: 8 }} />
        Daily Clinical Intake
      </Title>
      <Paragraph type="secondary">
        Quickly record ICD-10 codes, symptoms, EBM summaries and source links.
        Gemini will auto-classify and expand abbreviations nightly.
      </Paragraph>

      {/* ── Entry form ────────────────────────────────────────────────────── */}
      <Card style={{ marginBottom: 24 }} title={<><PlusOutlined /> Add Entry</>}>
        <Form form={form} layout="vertical" onFinish={onAdd}>
          <Space wrap style={{ width: '100%' }}>
            <Form.Item name="entryType" label="Type" rules={[{ required: true }]} style={{ minWidth: 130 }}>
              <Select placeholder="Entry type">
                {ENTRY_TYPES.map(t => (
                  <Select.Option key={t} value={t}>
                    <Tag color={typeColor[t]}>{t}</Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="icd10Code" label="ICD-10 Code" style={{ minWidth: 120 }}>
              <Input placeholder="e.g. I63" />
            </Form.Item>

            <Form.Item name="examDate" label="Exam Date" style={{ minWidth: 160 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item name="sourceName" label="Source / Journal" style={{ minWidth: 180 }}>
              <Input placeholder="e.g. NEJM, UpToDate" />
            </Form.Item>

            <Form.Item name="sourceUrl" label="URL / DOI" style={{ minWidth: 240 }}>
              <Input placeholder="https://pubmed.ncbi.nlm.nih.gov/…" />
            </Form.Item>

            <Form.Item name="tags" label="Tags (comma-separated)" style={{ minWidth: 200 }}>
              <Input placeholder="stroke, anticoagulation" />
            </Form.Item>
          </Space>

          <Form.Item name="rawText" label="Clinical Note" rules={[{ required: true }]}>
            <TextArea
              rows={3}
              placeholder="e.g. Pt with AF presented with Rt MCA ischaemic stroke. Started LMWH bridge, plan OAC after 2wk. NIHSS 8."
            />
          </Form.Item>

          <Form.Item name="ebmStatement" label="EBM Statement (optional)">
            <TextArea
              rows={2}
              placeholder="Paste the evidence statement or guideline recommendation here…"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={submitting} icon={<PlusOutlined />}>
              Save Entry
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* ── Browse / filter panel ─────────────────────────────────────────── */}
      <Divider />
      <Title level={4}>
        <SearchOutlined style={{ marginRight: 8 }} />
        Browse Entries
      </Title>

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
          style={{ width: 120 }}
          value={filterIcd10}
          onChange={e => setFilterIcd10(e.target.value)}
        />
        <Input
          placeholder="Gemini category"
          style={{ width: 180 }}
          value={filterCategory}
          onChange={e => setFilterCategory(e.target.value)}
        />
        <Button icon={<SearchOutlined />} onClick={fetchEntries}>Search</Button>
      </Space>

      <Table
        dataSource={entries}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 15 }}
        size="small"
        scroll={{ x: 900 }}
      />
    </div>
  );
};

export default DailyIntakePage;
