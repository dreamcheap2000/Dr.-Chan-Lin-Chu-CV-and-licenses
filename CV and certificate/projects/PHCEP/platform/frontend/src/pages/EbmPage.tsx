import React, { useState } from 'react';
import { Input, Button, Table, Form, Typography, message } from 'antd';
import axios from 'axios';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const columns = [
  { title: 'Statement', dataIndex: 'statement', key: 'statement', ellipsis: true },
  { title: 'PMID', dataIndex: 'pmid', key: 'pmid',
    render: (v: string) => v ? <a href={`https://pubmed.ncbi.nlm.nih.gov/${v}`} target="_blank" rel="noopener noreferrer">{v}</a> : '-' },
  { title: 'Specialty', dataIndex: 'specialty', key: 'specialty' },
  { title: 'ICD-10', dataIndex: 'icd10Codes', key: 'icd10' },
];

const EbmPage: React.FC = () => {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchForm] = Form.useForm();
  const [addForm] = Form.useForm();
  const [adding, setAdding] = useState(false);

  const onSearch = async (values: { q: string }) => {
    setLoading(true);
    try {
      const resp = await axios.get('/api/ebm/semantic-search', { params: { q: values.q } });
      setResults(resp.data);
    } catch {
      message.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const onAdd = async (values: any) => {
    setAdding(true);
    try {
      await axios.post('/api/ebm', values);
      message.success('EBM entry added');
      addForm.resetFields();
    } catch {
      message.error('Failed to add EBM entry');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div>
      <Title level={3}>EBM Knowledge Base</Title>

      <Form form={searchForm} layout="inline" onFinish={onSearch} style={{ marginBottom: 24 }}>
        <Form.Item name="q" rules={[{ required: true }]}>
          <Input placeholder="Search EBM statements..." style={{ width: 360 }} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>Semantic Search</Button>
        </Form.Item>
      </Form>

      <Table dataSource={results} columns={columns} rowKey="id" loading={loading} size="small" />

      <Title level={4} style={{ marginTop: 32 }}>Add EBM Entry (HCP / Admin)</Title>
      <Form form={addForm} layout="vertical" onFinish={onAdd} style={{ maxWidth: 600 }}>
        <Form.Item name="statement" label="Clinical Statement" rules={[{ required: true }]}>
          <TextArea rows={3} />
        </Form.Item>
        <Form.Item name="pmid" label="PMID"><Input placeholder="12345678" /></Form.Item>
        <Form.Item name="articleUrl" label="Article URL"><Input placeholder="https://..." /></Form.Item>
        <Form.Item name="icd10Codes" label="ICD-10 Codes"><Input placeholder="E11, E11.9" /></Form.Item>
        <Form.Item name="specialty" label="Specialty"><Input placeholder="Endocrinology" /></Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={adding}>Add Entry</Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default EbmPage;
