import React, { useState } from 'react';
import { Form, Input, Select, Button, Card, Alert, Spin, Typography, Tag } from 'antd';
import axios from 'axios';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

interface QueryResult {
  id: string;
  status: string;
  aiAnswer?: string;
  hcpAnswer?: string;
  citations?: string;
}

const QueryPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (values: { queryText: string; icd10Code?: string }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await axios.post('/api/queries', values);
      setResult(resp.data);
    } catch (e: any) {
      setError(e.response?.data?.message || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const statusColor: Record<string, string> = {
    PENDING: 'orange',
    AI_ANSWERED: 'green',
    HCP_NOTIFIED: 'blue',
    HCP_ANSWERED: 'purple',
    CLOSED: 'default',
  };

  return (
    <div style={{ maxWidth: 700 }}>
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
        <Form.Item name="icd10Code" label="ICD-10 code (optional)">
          <Input placeholder="e.g. E11 (Type 2 diabetes mellitus)" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Submit Query
          </Button>
        </Form.Item>
      </Form>

      {error && <Alert type="error" message={error} showIcon style={{ marginTop: 16 }} />}

      {result && (
        <Card style={{ marginTop: 24 }} title="Query Result">
          <Text type="secondary">Query ID: {result.id}</Text>
          <br />
          <Tag color={statusColor[result.status] || 'default'} style={{ margin: '8px 0' }}>
            {result.status}
          </Tag>
          {result.aiAnswer && (
            <>
              <Title level={5}>AI Answer</Title>
              <Paragraph>{result.aiAnswer}</Paragraph>
            </>
          )}
          {result.hcpAnswer && (
            <>
              <Title level={5}>Healthcare Professional Answer</Title>
              <Paragraph>{result.hcpAnswer}</Paragraph>
            </>
          )}
          {result.citations && (
            <>
              <Text type="secondary">Citations: {result.citations}</Text>
            </>
          )}
          {result.status === 'HCP_NOTIFIED' && (
            <Alert
              type="info"
              message="Your query has been forwarded to a healthcare professional. You will be notified when an answer is available."
              showIcon
              style={{ marginTop: 12 }}
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default QueryPage;
