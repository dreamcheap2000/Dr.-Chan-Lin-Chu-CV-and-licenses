import React, { useState } from 'react';
import { Form, Input, Select, Button, Table, DatePicker, InputNumber, Typography, Space, message } from 'antd';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title } = Typography;

const observationTypes = [
  'LAB', 'VITAL_SIGN', 'IMAGING_FINDING', 'SYMPTOM', 'MEDICATION', 'PROCEDURE', 'OTHER',
];

const columns = [
  { title: 'Date', dataIndex: 'effectiveDateTime', key: 'date',
    render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
  { title: 'Type', dataIndex: 'observationType', key: 'type' },
  { title: 'LOINC', dataIndex: 'loincCode', key: 'loinc' },
  { title: 'Observation', dataIndex: 'observationText', key: 'text', ellipsis: true },
  { title: 'Value', dataIndex: 'numericValue', key: 'value',
    render: (v: number, r: any) => v != null ? `${v} ${r.unit || ''}` : '-' },
];

const ObservationsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const resp = await axios.get('/api/patient/observations');
      setRecords(resp.data);
    } catch {
      message.error('Failed to load observations');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { fetchRecords(); }, []);

  const onAdd = async (values: any) => {
    setSubmitting(true);
    try {
      await axios.post('/api/patient/observations', {
        ...values,
        effectiveDateTime: values.effectiveDateTime?.toISOString(),
      });
      message.success('Observation recorded');
      form.resetFields();
      fetchRecords();
    } catch {
      message.error('Failed to record observation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Title level={3}>Health Records</Title>
      <Form form={form} layout="inline" onFinish={onAdd} style={{ marginBottom: 24, flexWrap: 'wrap', gap: 8 }}>
        <Form.Item name="observationType" rules={[{ required: true }]}>
          <Select placeholder="Type" style={{ width: 160 }}>
            {observationTypes.map(t => <Select.Option key={t}>{t}</Select.Option>)}
          </Select>
        </Form.Item>
        <Form.Item name="loincCode"><Input placeholder="LOINC code" style={{ width: 120 }} /></Form.Item>
        <Form.Item name="observationText" rules={[{ required: true }]}>
          <Input placeholder="Description / finding" style={{ width: 280 }} />
        </Form.Item>
        <Form.Item name="numericValue"><InputNumber placeholder="Value" style={{ width: 90 }} /></Form.Item>
        <Form.Item name="unit"><Input placeholder="Unit" style={{ width: 80 }} /></Form.Item>
        <Form.Item name="effectiveDateTime"><DatePicker showTime /></Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting}>Add</Button>
        </Form.Item>
      </Form>

      <Table
        dataSource={records}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 15 }}
        size="small"
      />
    </div>
  );
};

export default ObservationsPage;
