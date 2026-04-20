import React, { useState, useEffect } from 'react';
import {
  Typography, Form, Input, Select, Button, Space, Divider,
  Card, Tag, AutoComplete, message, Modal, List, Popconfirm, Row, Col, Tooltip,
} from 'antd';
import {
  PlusOutlined, SaveOutlined, DeleteOutlined, FileTextOutlined,
  BookOutlined, TagOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import ICD_CN_2023, { icdLabel, icdShortLabel } from '../data/icd_cn_2023';

const { Title, Text } = Typography;
const { TextArea } = Input;

// ── Types ─────────────────────────────────────────────────────────────────────

interface SoapNote {
  category: string;
  icdCodes: string[];
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

interface SoapTemplate {
  id?: string;
  name: string;
  category: string;
  content: string;
}

type SoapSection = 'subjective' | 'objective' | 'assessment' | 'plan';

// ── Constants ─────────────────────────────────────────────────────────────────

const SOAP_CATEGORIES = [
  '神經科 Neurology',
  '腦血管科 Cerebrovascular',
  '癲癇科 Epilepsy',
  '頭痛門診 Headache',
  '失智/認知 Dementia/Cognitive',
  '帕金森/運動疾患 Movement Disorders',
  '神經調控 Neuromodulation',
  '急症 Emergency',
  '一般科 General',
];

const SECTION_LABELS: Record<SoapSection, string> = {
  subjective: '主觀 Subjective (S)',
  objective:  '客觀 Objective (O)',
  assessment: '評估 Assessment (A)',
  plan:       '計畫 Plan (P)',
};

const SECTION_PLACEHOLDERS: Record<SoapSection, string> = {
  subjective: '主訴、現病史、過去病史…',
  objective:  '生命徵象、神經學檢查、影像/檢驗結果…',
  assessment: '診斷、鑑別診斷、病情評估…',
  plan:       '治療計畫、藥物處方、追蹤事項…',
};

const SOAP_SECTIONS: SoapSection[] = ['subjective', 'objective', 'assessment', 'plan'];

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build ICD autocomplete options from search query */
const buildIcdOptions = (q: string) => {
  if (!q) return [];
  const lower = q.toLowerCase();
  return ICD_CN_2023
    .filter(e =>
      e.code.toLowerCase().startsWith(lower) ||
      e.cn.includes(q) ||
      e.en.toLowerCase().includes(lower),
    )
    .slice(0, 20)
    .map(e => ({ value: icdShortLabel(e), label: icdLabel(e) }));
};

/**
 * Extract only the part before the first ":" in a template name.
 * e.g. "急性腦中風: 標準處置"  →  "急性腦中風"
 *      "NIHSS評分"            →  "NIHSS評分"
 */
function beforeColon(name: string): string {
  const idx = name.indexOf(':');
  return idx > 0 ? name.slice(0, idx).trim() : name.trim();
}

// ── Component ──────────────────────────────────────────────────────────────────

const SoapNotePage: React.FC = () => {
  // ── SOAP note state ─────────────────────────────────────────────────────
  const [category, setCategory] = useState<string>(SOAP_CATEGORIES[0]);
  const [icdCodes, setIcdCodes] = useState<string[]>([]);
  const [icdSearch, setIcdSearch] = useState('');
  const [icdOptions, setIcdOptions] = useState<{ value: string; label: string }[]>([]);
  const [note, setNote] = useState<Record<SoapSection, string>>({
    subjective: '', objective: '', assessment: '', plan: '',
  });

  // ── Template state ──────────────────────────────────────────────────────
  const [templates, setTemplates] = useState<SoapTemplate[]>([]);
  const [tplModalOpen, setTplModalOpen] = useState(false);
  const [newTplName, setNewTplName] = useState('');
  const [newTplContent, setNewTplContent] = useState('');
  const [newTplCategory, setNewTplCategory] = useState(SOAP_CATEGORIES[0]);

  // Per-section template ghost autocomplete
  const [activeTplSection, setActiveTplSection] = useState<SoapSection | null>(null);
  const [tplSearch, setTplSearch] = useState('');

  // ── Load templates on mount ─────────────────────────────────────────────
  useEffect(() => { fetchTemplates(); }, []);

  const fetchTemplates = async () => {
    try {
      const resp = await axios.get('/api/soap-templates');
      setTemplates(resp.data);
    } catch { /* backend may be offline in dev */ }
  };

  // ── ICD helpers ─────────────────────────────────────────────────────────

  const handleIcdSearch = (val: string) => {
    setIcdSearch(val);
    setIcdOptions(buildIcdOptions(val));
  };

  /** Append ICD code — no duplicates, no replacement */
  const handleIcdSelect = (val: string) => {
    const code = val.split(' ')[0];
    if (!icdCodes.includes(code)) {
      setIcdCodes(prev => [...prev, code]);
    }
    setIcdSearch('');
    setIcdOptions([]);
  };

  // ── Template ghost helpers ───────────────────────────────────────────────

  /**
   * Build template options for the ghost window.
   * ONLY templates whose category matches the current note's category are shown.
   */
  const ghostOptions = (q: string) => {
    return templates
      .filter(t => {
        if (t.category !== category) return false;
        if (!q) return true;
        return t.name.toLowerCase().includes(q.toLowerCase()) ||
               t.content.toLowerCase().includes(q.toLowerCase());
      })
      .slice(0, 10)
      .map(t => ({
        value: t.name,
        label: (
          <Tooltip title={t.content} placement="right">
            <Space>
              <TagOutlined />
              <span style={{ fontWeight: 500 }}>{beforeColon(t.name)}</span>
              {t.name.includes(':') && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {t.name.slice(t.name.indexOf(':') + 1).trim()}
                </Text>
              )}
            </Space>
          </Tooltip>
        ),
      }));
  };

  /**
   * Insert template: appends ONLY the text before ":" to the section.
   * Does NOT replace existing content.
   */
  const insertTemplate = (val: string, section: SoapSection) => {
    const insert = beforeColon(val);
    setNote(prev => ({
      ...prev,
      [section]: prev[section] ? prev[section] + '\n' + insert : insert,
    }));
    setTplSearch('');
    setActiveTplSection(null);
  };

  // ── Save SOAP note ───────────────────────────────────────────────────────
  const handleSaveNote = async () => {
    const payload: SoapNote = { category, icdCodes, ...note };
    try {
      await axios.post('/api/soap-notes', payload);
      message.success('SOAP 病歷記錄已儲存');
    } catch {
      message.warning('後端儲存失敗（開發模式下可忽略）');
    }
  };

  // ── Template management ──────────────────────────────────────────────────
  const handleSaveTemplate = async () => {
    if (!newTplName.trim() || !newTplContent.trim()) {
      message.error('請填寫範本名稱與內容');
      return;
    }
    const tpl: SoapTemplate = {
      name: newTplName.trim(),
      category: newTplCategory,
      content: newTplContent.trim(),
    };
    try {
      const resp = await axios.post('/api/soap-templates', tpl);
      setTemplates(prev => [...prev, resp.data]);
    } catch {
      setTemplates(prev => [...prev, { ...tpl, id: `local-${Date.now()}` }]);
      message.warning('已本地儲存範本（後端離線）');
    }
    setNewTplName('');
    setNewTplContent('');
    setTplModalOpen(false);
    message.success('範本已儲存');
  };

  const handleDeleteTemplate = async (tpl: SoapTemplate) => {
    if (tpl.id && !tpl.id.startsWith('local-')) {
      try { await axios.delete(`/api/soap-templates/${tpl.id}`); } catch { /* silent */ }
    }
    setTemplates(prev => prev.filter(t => !(t.id === tpl.id && t.name === tpl.name)));
    message.success('範本已刪除');
  };

  const categoryTemplateCount = templates.filter(t => t.category === category).length;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div>
      <Title level={3}>
        <FileTextOutlined style={{ marginRight: 8 }} />
        SOAP 病歷記錄
      </Title>

      {/* ── Category & ICD selector ────────────────────────────────────────── */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} wrap>
          <Col xs={24} md={8}>
            <Form.Item label="科別類別" style={{ marginBottom: 0 }}>
              <Select
                value={category}
                onChange={setCategory}
                style={{ width: '100%' }}
                options={SOAP_CATEGORIES.map(c => ({ value: c, label: c }))}
              />
            </Form.Item>
          </Col>
          <Col xs={24} md={16}>
            <Form.Item label="ICD-10 診斷碼（可多選追加，不會覆蓋）" style={{ marginBottom: 0 }}>
              <AutoComplete
                value={icdSearch}
                options={icdOptions}
                onSearch={handleIcdSearch}
                onSelect={handleIcdSelect}
                placeholder="搜尋 ICD 代碼或中文名稱…"
                style={{ width: '100%', marginBottom: 6 }}
                allowClear
                onClear={() => { setIcdSearch(''); setIcdOptions([]); }}
              />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {icdCodes.map(code => (
                  <Tag
                    key={code}
                    closable
                    color="blue"
                    onClose={() => setIcdCodes(prev => prev.filter(c => c !== code))}
                  >
                    {code}
                  </Tag>
                ))}
              </div>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* ── Template action bar ─────────────────────────────────────────────── */}
      <Space style={{ marginBottom: 12 }}>
        <Button icon={<BookOutlined />} onClick={() => setTplModalOpen(true)}>
          管理範本
        </Button>
        <Text type="secondary" style={{ fontSize: 12 }}>
          目前類別「{category}」共 {categoryTemplateCount} 個範本
        </Text>
      </Space>

      {/* ── SOAP sections ───────────────────────────────────────────────────── */}
      {SOAP_SECTIONS.map(section => (
        <Card
          key={section}
          size="small"
          title={<Text strong>{SECTION_LABELS[section]}</Text>}
          style={{ marginBottom: 12 }}
          extra={
            /* Ghost window: only shows saved templates in the current category */
            <AutoComplete
              value={activeTplSection === section ? tplSearch : ''}
              options={ghostOptions(activeTplSection === section ? tplSearch : '')}
              onSearch={val => { setActiveTplSection(section); setTplSearch(val); }}
              onSelect={val => insertTemplate(val, section)}
              onFocus={() => { setActiveTplSection(section); setTplSearch(''); }}
              onBlur={() => { setTimeout(() => { setActiveTplSection(null); setTplSearch(''); }, 200); }}
              placeholder="套用範本…"
              style={{ width: 200 }}
              allowClear
              onClear={() => { setTplSearch(''); setActiveTplSection(null); }}
            />
          }
        >
          <TextArea
            rows={4}
            value={note[section]}
            onChange={e => setNote(prev => ({ ...prev, [section]: e.target.value }))}
            placeholder={SECTION_PLACEHOLDERS[section]}
            style={{ fontFamily: 'monospace', fontSize: 13 }}
          />
        </Card>
      ))}

      <Divider />
      <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveNote} size="large">
        儲存 SOAP 病歷
      </Button>

      {/* ── Template management modal ──────────────────────────────────────── */}
      <Modal
        title={
          <Space>
            <BookOutlined />
            SOAP 範本管理
          </Space>
        }
        open={tplModalOpen}
        onCancel={() => setTplModalOpen(false)}
        footer={null}
        width={680}
      >
        {/* Add new template */}
        <Card size="small" title={<><PlusOutlined /> 新增範本</>} style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Input
              placeholder='範本名稱（建議格式：「短標籤: 說明」）'
              value={newTplName}
              onChange={e => setNewTplName(e.target.value)}
            />
            <Select
              value={newTplCategory}
              onChange={setNewTplCategory}
              style={{ width: '100%' }}
              options={SOAP_CATEGORIES.map(c => ({ value: c, label: c }))}
            />
            <TextArea
              rows={3}
              placeholder="範本內容（套用時追加至 SOAP 段落，不覆蓋現有內容）"
              value={newTplContent}
              onChange={e => setNewTplContent(e.target.value)}
            />
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveTemplate}>
              儲存範本
            </Button>
          </Space>
        </Card>

        <Divider orientation="left">
          已儲存範本（{category}）
        </Divider>

        {/* Only show templates in the current category */}
        <List
          size="small"
          dataSource={templates.filter(t => t.category === category)}
          locale={{ emptyText: '此類別尚無儲存範本' }}
          renderItem={tpl => (
            <List.Item
              actions={[
                <Popconfirm
                  title="確定刪除此範本？"
                  onConfirm={() => handleDeleteTemplate(tpl)}
                  okText="刪除"
                  cancelText="取消"
                >
                  <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text strong>{beforeColon(tpl.name)}</Text>
                    {tpl.name.includes(':') && (
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {tpl.name.slice(tpl.name.indexOf(':') + 1).trim()}
                      </Text>
                    )}
                  </Space>
                }
                description={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {tpl.content.length > 80 ? tpl.content.slice(0, 80) + '…' : tpl.content}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};

export default SoapNotePage;
