import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const DataChart = ({ data, chartType = 'bar' }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return <p>No data available for visualization</p>;
  }

  const columns = Object.keys(data[0]);
  
  // Find numeric columns for y-axis
  const numericColumns = columns.filter(col => 
    data.every(row => !isNaN(parseFloat(row[col])) && isFinite(row[col]))
  );
  
  // Find categorical columns for x-axis
  const categoricalColumns = columns.filter(col => !numericColumns.includes(col));
  
  if (numericColumns.length === 0) {
    return <p>No numeric data found for visualization</p>;
  }

  const xColumn = categoricalColumns[0] || columns[0];
  const yColumn = numericColumns[0];

  const labels = data.map(row => String(row[xColumn]));
  const values = data.map(row => parseFloat(row[yColumn]) || 0);

  const chartData = {
    labels,
    datasets: [
      {
        label: yColumn,
        data: values,
        backgroundColor: chartType === 'pie' ? [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
        ] : 'rgba(54, 162, 235, 0.8)',
        borderColor: chartType === 'pie' ? [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
        ] : 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${yColumn} by ${xColumn}`,
      },
    },
    scales: chartType !== 'pie' ? {
      y: {
        beginAtZero: true,
      },
    } : undefined,
  };

  const ChartComponent = chartType === 'line' ? Line : chartType === 'pie' ? Pie : Bar;

  return (
    <div className="chart-container">
      <ChartComponent data={chartData} options={options} />
    </div>
  );
};

export default DataChart;
