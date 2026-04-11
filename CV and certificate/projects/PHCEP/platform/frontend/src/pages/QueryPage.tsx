import React, { useState } from 'react';
import {
  Form, Input, Select, Button, Card, Alert, Spin, Typography, Tag, Progress,
  Collapse, Tooltip, InputNumber, Space, Divider,
} from 'antd';
import {
  CheckCircleOutlined, WarningOutlined, LinkOutlined, ExperimentOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

interface MatchItem {
  rank: number;
  text: string;
  confidence: number;
  citation: string;
  source: string;
  url: string;
}

interface QueryResult {
  id: string;
  status: string;
  aiAnswer?: string;
  hcpAnswer?: string;
  citations?: string;
  topKMatchesJson?: string;
  confidence?: number;
}

const confidenceColor = (score: number) =>
  score >= 0.75 ? '#52c41a' : score >= 0.5 ? '#faad14' : '#ff4d4f';

const sourceIcon = (source: string) =>
  source === 'ebm' ? <ExperimentOutlined /> : <MedicineBoxOutlined />;

const statusColor: Record<string, string> = {
  PENDING: 'orange',
  AI_ANSWERED: 'green',
  HCP_NOTIFIED: 'blue',
  HCP_ANSWERED: 'purple',
  CLOSED: 'default',
};

const QueryPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState<number>(3);

  const onSubmit = async (values: { queryText: string; icd10Code?: string }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await axios.post('/api/queries', { ...values, topK });
      setResult(resp.data);
    } catch (e: any) {
      setError(e.response?.data?.message || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const parseMatches = (json?: string): MatchItem[] => {
    if (!json) return [];
    try { return JSON.parse(json) as MatchItem[]; } catch { return []; }
  };

  const matches = parseMatches(result?.topKMatchesJson);

  return (
    <div style={{ maxWidth: 760 }}>
      <Title level={3}>Submit a Medical Query</Title>
      <Paragraph type="secondary">
        Ask a health question or describe a symptom. Our AI will synthesise an answer from
        your health history and evidence-based sources. If the confidence is low, a healthcare
        professional will be notified.
      </Paragraph>

      <Form form={form} layout="vertical" onFinish={onSubmit}>
        <Form.Item
          name="queryText"
          label="Your question"
          rules={[{ required: true, message: 'Please enter your question' }]}
        >
          <TextArea rows={4} placeholder="e.g. My HbA1c is 7.2% — what does this mean for my diabetes management?" />
        </Form.Item>

        <Space align="start" style={{ width: '100%', justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <Form.Item name="icd10Code" label="ICD-10 code (optional)" style={{ flex: 1, minWidth: 240 }}>
            <Input placeholder="e.g. E11 (Type 2 diabetes mellitus)" />
          </Form.Item>
          <Form.Item label={`Top results to show: ${topK}`} style={{ minWidth: 200 }}>
            <InputNumber
              min={1}
              max={10}
              value={topK}
              onChange={v => setTopK(v ?? 3)}
              style={{ width: 80 }}
            />
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
              (1–10, dynamic)
            </Text>
          </Form.Item>
        </Space>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Submit Query
          </Button>
        </Form.Item>
      </Form>

      {error && <Alert type="error" message={error} showIcon style={{ marginTop: 16 }} />}

      {loading && <Spin tip="Analysing your query…" style={{ marginTop: 24, display: 'block' }} />}

      {result && (
        <div style={{ marginTop: 24 }}>
          <Card
            title={
              <Space>
                <span>Query Result</span>
                <Tag color={statusColor[result.status] || 'default'}>{result.status}</Tag>
                {result.confidence != null && (
                  <Tooltip title={`ML confidence: ${(result.confidence * 100).toFixed(1)}%`}>
                    <Tag color={confidenceColor(result.confidence)} icon={<CheckCircleOutlined />}>
                      {(result.confidence * 100).toFixed(0)}% confidence
                    </Tag>
                  </Tooltip>
                )}
              </Space>
            }
          >
            <Text type="secondary">Query ID: {result.id}</Text>

            {result.aiAnswer && (
              <>
                <Divider orientation="left">AI Answer</Divider>
                <Paragraph style={{ whiteSpace: 'pre-line' }}>{result.aiAnswer}</Paragraph>
              </>
            )}

            {result.hcpAnswer && (
              <>
                <Divider orientation="left">Healthcare Professional Answer</Divider>
                <Paragraph>{result.hcpAnswer}</Paragraph>
              </>
            )}

            {result.citations && (
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                Citations: {result.citations}
              </Text>
            )}

            {result.status === 'HCP_NOTIFIED' && (
              <Alert
                type="info"
                icon={<WarningOutlined />}
                message="Forwarded to a healthcare professional"
                description="The AI confidence was below the threshold. A healthcare professional will review your query and respond."
                showIcon
                style={{ marginTop: 12 }}
              />
            )}
          </Card>

          {/* ── Top-K ranked match cards ─────────────────────────────────── */}
          {matches.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Title level={5} style={{ marginBottom: 12 }}>
                Top {matches.length} ranked evidence matches
              </Title>
              <Collapse accordion ghost>
                {matches.map(m => (
                  <Panel
                    key={m.rank}
                    header={
                      <Space style={{ width: '100%', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                        <Space>
                          {sourceIcon(m.source)}
                          <Text strong>#{m.rank}</Text>
                          <Tag color={m.source === 'ebm' ? 'blue' : 'green'}>
                            {m.source === 'ebm' ? 'EBM' : 'Observation'}
                          </Tag>
                          <Text ellipsis style={{ maxWidth: 340 }}>{m.text}</Text>
                        </Space>
                        <Tooltip title={`${(m.confidence * 100).toFixed(1)}% match`}>
                          <Progress
                            percent={Math.round(m.confidence * 100)}
                            strokeColor={confidenceColor(m.confidence)}
                            size="small"
                            style={{ width: 120 }}
                          />
                        </Tooltip>
                      </Space>
                    }
                  >
                    <Paragraph style={{ margin: 0 }}>{m.text}</Paragraph>
                    {m.citation && (
                      <Text type="secondary" style={{ display: 'block', marginTop: 6 }}>
                        Citation: {m.citation}
                      </Text>
                    )}
                    {m.url && (
                      <a href={m.url} target="_blank" rel="noopener noreferrer" style={{ marginTop: 4, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <LinkOutlined /> View source
                      </a>
                    )}
                  </Panel>
                ))}
              </Collapse>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QueryPage;
