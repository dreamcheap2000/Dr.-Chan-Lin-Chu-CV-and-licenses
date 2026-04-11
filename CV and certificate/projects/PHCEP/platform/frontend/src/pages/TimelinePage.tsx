import React, { useEffect, useState } from 'react';
import { Typography, Spin, Empty } from 'antd';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title } = Typography;

const TimelinePage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/patient/observations/timeline')
      .then(resp => {
        const formatted = resp.data
          .filter((r: any) => r.numericValue != null)
          .map((r: any) => ({
            date: dayjs(r.effectiveDateTime).format('MM-DD'),
            value: r.numericValue,
            unit: r.unit,
            label: r.loincCode || r.observationType,
          }));
        setData(formatted);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ marginTop: 60 }} />;
  if (!data.length) return <Empty description="No numeric observations found. Add lab values or vitals to see your timeline." />;

  return (
    <div>
      <Title level={3}>Longitudinal Health Timeline</Title>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip formatter={(value, _name, props) => [`${value} ${props.payload.unit || ''}`, props.payload.label]} />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#1677ff" dot={true} name="Value" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TimelinePage;
