import React, { useEffect, useState } from 'react';
import {
  Typography, Table, Tag, Card, Row, Col, Statistic, Button, Select,
  DatePicker, Space, Modal, Descriptions, message, Tooltip,
} from 'antd';
import {
  CheckCircleOutlined, WarningOutlined, TeamOutlined, MessageOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

interface AuditEntry {
  id: string;
  queryId: string;
  recipientToken: string;
  messageType: 'AI_ANSWER' | 'HCP_ESCALATION' | 'HCP_ANSWER_RELAY';
  messageContent: string;
  confidence: number | null;
  topKMatchesJson: string | null;
  queryText: string;
  sentAt: string;
}

interface Stats {
  totalMessages: number;
  aiAnswers: number;
  hcpEscalations: number;
  hcpAnswerRelays: number;
}

const typeColors: Record<string, string> = {
  AI_ANSWER: 'green',
  HCP_ESCALATION: 'orange',
  HCP_ANSWER_RELAY: 'purple',
};

const typeIcons: Record<string, React.ReactNode> = {
  AI_ANSWER: <CheckCircleOutlined />,
  HCP_ESCALATION: <WarningOutlined />,
  HCP_ANSWER_RELAY: <TeamOutlined />,
};

const AdminPage: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [detail, setDetail] = useState<AuditEntry | null>(null);

  const fetchStats = async () => {
    try {
      const resp = await axios.get('/api/admin/audit-log/stats');
      setStats(resp.data);
    } catch {
      /* stats are optional; don't block the main table */
    }
  };

  const fetchEntries = async (p = page, ps = pageSize) => {
    setLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(p),
        size: String(ps),
      };
      if (typeFilter) params.type = typeFilter;
      if (dateRange) {
        params.from = dateRange[0].toISOString();
        params.to = dateRange[1].toISOString();
      }
      const resp = await axios.get('/api/admin/audit-log', { params });
      setEntries(resp.data.content);
      setTotal(resp.data.totalElements);
    } catch (e: any) {
      message.error('Failed to load audit log: ' + (e.response?.data?.message || e.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchEntries(0, pageSize);
  }, []);

  const parseMatches = (json: string | null) => {
    if (!json) return [];
    try { return JSON.parse(json); } catch { return []; }
  };

  const columns = [
    {
      title: 'Sent At',
      dataIndex: 'sentAt',
      key: 'sentAt',
      width: 160,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Type',
      dataIndex: 'messageType',
      key: 'type',
      width: 160,
      render: (v: string) => (
        <Tag icon={typeIcons[v]} color={typeColors[v] || 'default'}>{v}</Tag>
      ),
    },
    {
      title: 'Query',
      dataIndex: 'queryText',
      key: 'query',
      ellipsis: true,
      render: (v: string) => <Tooltip title={v}><Text ellipsis style={{ maxWidth: 260 }}>{v}</Text></Tooltip>,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'conf',
      width: 110,
      render: (v: number | null) =>
        v != null ? (
          <Tag color={v >= 0.75 ? 'green' : v >= 0.5 ? 'orange' : 'red'}>
            {(v * 100).toFixed(0)}%
          </Tag>
        ) : '—',
    },
    {
      title: 'Recipient Token',
      dataIndex: 'recipientToken',
      key: 'token',
      width: 200,
      ellipsis: true,
      render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: any, row: AuditEntry) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => setDetail(row)}
          aria-label="View details"
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>
        <MessageOutlined style={{ marginRight: 8 }} />
        Platform Manager — AI Message Audit Log
      </Title>
      <Paragraph type="secondary">
        Every automated message sent to users by the AI or relayed from HCPs is recorded here.
        Use the filters below to audit communications by type, date, or confidence threshold.
      </Paragraph>

      {/* ── Summary stats ──────────────────────────────────────────────────── */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6}>
            <Card><Statistic title="Total Messages" value={stats.totalMessages} prefix={<MessageOutlined />} /></Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card><Statistic title="AI Answered" value={stats.aiAnswers} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card><Statistic title="HCP Escalations" value={stats.hcpEscalations} valueStyle={{ color: '#faad14' }} prefix={<WarningOutlined />} /></Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card><Statistic title="HCP Answer Relays" value={stats.hcpAnswerRelays} valueStyle={{ color: '#722ed1' }} prefix={<TeamOutlined />} /></Card>
          </Col>
        </Row>
      )}

      {/* ── Filters ────────────────────────────────────────────────────────── */}
      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by type"
          allowClear
          style={{ width: 200 }}
          value={typeFilter}
          onChange={v => setTypeFilter(v)}
          options={[
            { value: 'AI_ANSWER', label: 'AI Answer' },
            { value: 'HCP_ESCALATION', label: 'HCP Escalation' },
            { value: 'HCP_ANSWER_RELAY', label: 'HCP Answer Relay' },
          ]}
        />
        <RangePicker
          showTime
          onChange={v => setDateRange(v as [dayjs.Dayjs, dayjs.Dayjs] | null)}
        />
        <Button
          type="primary"
          onClick={() => { setPage(0); fetchEntries(0, pageSize); fetchStats(); }}
        >
          Apply
        </Button>
        <Button onClick={() => { setTypeFilter(undefined); setDateRange(null); setPage(0); fetchEntries(0, pageSize); }}>
          Reset
        </Button>
      </Space>

      {/* ── Audit log table ────────────────────────────────────────────────── */}
      <Table
        dataSource={entries}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page + 1,
          pageSize,
          total,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onChange: (p, ps) => {
            setPage(p - 1);
            setPageSize(ps);
            fetchEntries(p - 1, ps);
          },
        }}
        size="small"
        scroll={{ x: 900 }}
      />

      {/* ── Detail modal ───────────────────────────────────────────────────── */}
      <Modal
        title="Audit Entry Detail"
        open={!!detail}
        onCancel={() => setDetail(null)}
        footer={null}
        width={700}
      >
        {detail && (
          <>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="ID"><Text code>{detail.id}</Text></Descriptions.Item>
              <Descriptions.Item label="Query ID"><Text code>{detail.queryId}</Text></Descriptions.Item>
              <Descriptions.Item label="Recipient Token"><Text code>{detail.recipientToken}</Text></Descriptions.Item>
              <Descriptions.Item label="Type">
                <Tag icon={typeIcons[detail.messageType]} color={typeColors[detail.messageType]}>{detail.messageType}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Sent At">{dayjs(detail.sentAt).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="Confidence">
                {detail.confidence != null ? `${(detail.confidence * 100).toFixed(1)}%` : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Original Query">{detail.queryText}</Descriptions.Item>
              <Descriptions.Item label="Message Sent to User">
                <Paragraph style={{ whiteSpace: 'pre-line', margin: 0 }}>{detail.messageContent}</Paragraph>
              </Descriptions.Item>
            </Descriptions>

            {detail.topKMatchesJson && parseMatches(detail.topKMatchesJson).length > 0 && (
              <>
                <Title level={5} style={{ marginTop: 16 }}>Top-K Evidence Matches</Title>
                <Table
                  size="small"
                  dataSource={parseMatches(detail.topKMatchesJson)}
                  rowKey="rank"
                  pagination={false}
                  columns={[
                    { title: '#', dataIndex: 'rank', width: 40 },
                    { title: 'Source', dataIndex: 'source', width: 100,
                      render: (v: string) => <Tag color={v === 'ebm' ? 'blue' : 'green'}>{v.toUpperCase()}</Tag> },
                    { title: 'Text', dataIndex: 'text', ellipsis: true },
                    { title: 'Confidence', dataIndex: 'confidence', width: 100,
                      render: (v: number) => `${(v * 100).toFixed(1)}%` },
                    { title: 'Citation', dataIndex: 'citation', width: 120, ellipsis: true },
                  ]}
                />
              </>
            )}
          </>
        )}
      </Modal>
    </div>
  );
};

export default AdminPage;
