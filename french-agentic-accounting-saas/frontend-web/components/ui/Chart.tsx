'use client'

import { useEffect, useRef } from 'react'

interface ChartProps {
  data: any[]
  layout: any
  config?: any
  id: string
  className?: string
  style?: React.CSSProperties
}

export default function Chart({ data, layout, config, id, className, style }: ChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let Plotly: any

    const loadPlotly = async () => {
      Plotly = await import('plotly.js-dist-min')
      if (chartRef.current && Plotly) {
        Plotly.newPlot(chartRef.current, data, layout, {
          responsive: true,
          displayModeBar: false,
          displaylogo: false,
          ...config,
        })
      }
    }

    loadPlotly()

    const handleResize = () => {
      if (Plotly && chartRef.current) {
        Plotly.relayout(chartRef.current, {
          autosize: true,
          width: chartRef.current.offsetWidth,
          height: chartRef.current.offsetHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (Plotly && chartRef.current) {
        Plotly.purge(chartRef.current)
      }
    }
  }, [data, layout, config, id])

  return <div id={id} ref={chartRef} className={className} style={style} />
}
