'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ComposedChart, Area
} from 'recharts';
import { Calendar, DollarSign, ShoppingBag, TrendingUp, Package, Download, Lock, BrainCircuit, Activity, Clock, BarChart3, Filter } from 'lucide-react';
import { API_BASE, formatCurrency, cn } from '@/lib/utils';
import clsx from 'clsx';

export default function AnalyticsDashboard() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [pinInput, setPinInput] = useState('');

    // --- Controls State ---
    const defaultEnd = new Date().toISOString().split('T')[0];
    const defaultStart = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const [startDate, setStartDate] = useState(defaultStart);
    const [endDate, setEndDate] = useState(defaultEnd);
    const [metric, setMetric] = useState('revenue'); // 'revenue' | 'orders'
    const [freq, setFreq] = useState('D'); // 'H' | 'D' | 'W'
    const [categoryId, setCategoryId] = useState('');
    const [productId, setProductId] = useState('');
    const [isComparing, setIsComparing] = useState(false);
    const [activeTab, setActiveTab] = useState('historical'); // 'historical' | 'forecast'

    // --- Forecast State ---
    const [fcastModel, setFcastModel] = useState('xgboost'); // 'arima' | 'sklearn' | 'xgboost'
    const [fcastHorizon, setFcastHorizon] = useState(14);
    const [fcastIsRunning, setFcastIsRunning] = useState(false);
    const [fcastResult, setFcastResult] = useState<any>(null);

    // --- Data State ---
    const [categories, setCategories] = useState<any[]>([]);
    const [products, setProducts] = useState<any[]>([]);

    const [currData, setCurrData] = useState<any>(null);
    const [prevData, setPrevData] = useState<any>(null);
    const [topProducts, setTopProducts] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // --- Auth Check ---
    const handlePinSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const correctPin = process.env.NEXT_PUBLIC_ANALYTICS_PIN || '1234';
        if (pinInput === correctPin) {
            setIsAuthenticated(true);
        } else {
            alert('Incorrect PIN');
            setPinInput('');
        }
    };

    // --- Metadata Initial Load ---
    useEffect(() => {
        if (!isAuthenticated) return;
        fetch(`${API_BASE}/categories`).then(r => r.json()).then(setCategories).catch(console.error);
        fetch(`${API_BASE}/products`).then(r => r.json()).then(setProducts).catch(console.error);
    }, [isAuthenticated]);

    // --- Computed Previous Dates ---
    const prevDateRange = useMemo(() => {
        const dEnd = new Date(endDate);
        const dStart = new Date(startDate);
        const duration = dEnd.getTime() - dStart.getTime();

        const pEnd = new Date(dStart.getTime() - 24 * 60 * 60 * 1000);
        const pStart = new Date(pEnd.getTime() - duration);
        return {
            start: pStart.toISOString().split('T')[0],
            end: pEnd.toISOString().split('T')[0]
        };
    }, [startDate, endDate]);

    // --- Fetch Main Analytics ---
    const fetchAnalytics = async () => {
        setIsLoading(true);
        try {
            let filterString = `?metric=${metric}&freq=${freq}&start=${startDate}&end=${endDate}`;
            if (categoryId) filterString += `&category_id=${categoryId}`;
            if (productId) filterString += `&product_id=${productId}`;

            // Fetch Current Period TimeSeries
            const currRes = await fetch(`${API_BASE}/analytics/timeseries${filterString}`);
            if (currRes.ok) setCurrData(await currRes.json());

            // Fetch Top Products
            let topStr = `?start=${startDate}&end=${endDate}`;
            const topRes = await fetch(`${API_BASE}/analytics/top-products${topStr}`);
            if (topRes.ok) setTopProducts(await topRes.json());

            // Fetch Previous Period if Comparing
            if (isComparing) {
                let pFilter = `?metric=${metric}&freq=${freq}&start=${prevDateRange.start}&end=${prevDateRange.end}`;
                if (categoryId) pFilter += `&category_id=${categoryId}`;
                if (productId) pFilter += `&product_id=${productId}`;
                const pRes = await fetch(`${API_BASE}/analytics/timeseries${pFilter}`);
                if (pRes.ok) setPrevData(await pRes.json());
            } else {
                setPrevData(null);
            }

        } catch (e) {
            console.error("Error fetching analytics", e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isAuthenticated) {
            fetchAnalytics();
        }
    }, [isAuthenticated, metric, freq, startDate, endDate, categoryId, productId, isComparing]);

    // --- Run Forecast ---
    const runForecast = async () => {
        setFcastIsRunning(true);
        setFcastResult(null);
        try {
            const payload = {
                metric,
                freq,
                horizon: fcastHorizon,
                model: fcastModel,
                train_start: startDate,
                train_end: endDate,
                filters: {
                    ...(categoryId ? { category_id: parseInt(categoryId) } : {}),
                    ...(productId ? { product_id: parseInt(productId) } : {})
                },
                cv: { type: "rolling", splits: 3, step: 7 }
            };

            const res = await fetch(`${API_BASE}/forecast/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok) {
                alert(`Forecast Failed: ${data.error || 'Unknown error'}`);
            } else {
                setFcastResult(data);
            }
        } catch (e) {
            console.error(e);
            alert('Failed to connect to forecasting engine.');
        } finally {
            setFcastIsRunning(false);
        }
    };

    // --- Formatters & Helpers ---
    const valFormatter = (val: any) => metric === 'revenue' ? formatCurrency(val) : val;

    const exportCSV = () => {
        if (!currData || !currData.series) return;
        const headers = ["Date", metric.charAt(0).toUpperCase() + metric.slice(1)];
        const rows = currData.series.map((d: any) => [d.ds, metric === 'revenue' ? (d.y / 100).toFixed(2) : d.y]);

        const csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map((e: any) => e.join(",")).join("\n");
        const link = document.createElement("a");
        link.setAttribute("href", encodeURI(csvContent));
        link.setAttribute("download", `timeseries_${metric}_${startDate}_to_${endDate}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // --- Computed Chart Data ---
    const tsChartData = useMemo(() => {
        if (!currData || !currData.series) return [];
        if (!isComparing || !prevData || !prevData.series) {
            return currData.series.map((d: any) => ({ label: d.ds, Current: d.y }));
        }
        // Align currents and prevs by index for overlay
        return currData.series.map((d: any, i: number) => ({
            label: d.ds,
            Current: d.y,
            Previous: prevData.series[i] ? prevData.series[i].y : null
        }));
    }, [currData, prevData, isComparing]);

    const forecastChartData = useMemo(() => {
        if (!currData || !currData.series || !fcastResult || !fcastResult.forecast_series) return [];
        const hist = currData.series.map((d: any) => ({ date: d.ds, Actual: d.y }));

        // Ensure seamless line connection by duplicating the last history point into the forecast space
        const lastHist = hist.length > 0 ? hist[hist.length - 1] : null;
        let bridge: any[] = [];
        if (lastHist && fcastResult.forecast_series.length > 0) {
            const firstFcastDate = fcastResult.forecast_series[0].date.split(' ')[0];
            if (firstFcastDate !== lastHist.date) {
                bridge = [{ date: firstFcastDate, Actual: lastHist.Actual, Forecast: lastHist.Actual, lower: lastHist.Actual, upper: lastHist.Actual }];
            }
        }

        const fcast = fcastResult.forecast_series.map((d: any) => ({
            date: d.date.split(' ')[0],
            Forecast: d.yhat,
            lower: d.lower != null ? d.lower : d.yhat,
            upper: d.upper != null ? d.upper : d.yhat,
        }));

        const result = [...hist, ...bridge, ...fcast];
        return result;
    }, [currData, fcastResult]);

    // 1) Render PIN Gate
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-2xl shadow-sm border border-border max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8 text-primary" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Analytics Access</h2>
                    <p className="text-muted-foreground mb-6">Please enter the administrative PIN to view reports.</p>
                    <form onSubmit={handlePinSubmit}>
                        <input
                            type="password"
                            value={pinInput}
                            onChange={(e) => setPinInput(e.target.value)}
                            placeholder="Enter PIN"
                            className="w-full text-center text-2xl tracking-widest p-4 rounded-xl border border-border focus:ring-2 focus:ring-primary focus:outline-none mb-4"
                            maxLength={8}
                            autoFocus
                        />
                        <button type="submit" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-4 rounded-xl transition-colors">
                            Unlock Dashboard
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    // 2) Render Dashboard
    return (
        <div className="min-h-screen bg-gray-50 p-6 md:p-8">
            <div className="max-w-[1400px] mx-auto space-y-6">

                {/* Header Title */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold font-serif text-gray-900 flex items-center gap-3">
                            <Activity className="w-8 h-8 text-primary" /> Advanced Analytics
                        </h1>
                        <p className="text-muted-foreground mt-1">AI-powered store performance & sales metrics</p>
                    </div>
                    <button onClick={exportCSV} className="flex items-center gap-2 px-4 py-2 border border-border rounded-xl hover:bg-white transition-colors text-sm font-medium shadow-sm">
                        <Download className="w-4 h-4" /> Export CSV
                    </button>
                </div>

                {/* --- Master Control Panel --- */}
                <div className="bg-white p-4 rounded-2xl shadow-sm border border-border flex flex-wrap gap-4 items-center">
                    {/* Date Range */}
                    <div className="flex items-center gap-2 bg-gray-50 p-2 rounded-xl border border-border">
                        <Calendar className="w-4 h-4 text-gray-400 ml-1" />
                        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="bg-transparent text-sm font-medium outline-none" />
                        <span className="text-gray-300">→</span>
                        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="bg-transparent text-sm font-medium outline-none" />
                    </div>

                    {/* Metric & Freq */}
                    <div className="flex items-center gap-2">
                        <select className="bg-gray-50 border border-border text-sm font-medium rounded-xl p-2.5 outline-none" value={metric} onChange={(e) => setMetric(e.target.value)}>
                            <option value="revenue">Revenue Data</option>
                            <option value="orders">Orders Data</option>
                        </select>
                        <select className="bg-gray-50 border border-border text-sm font-medium rounded-xl p-2.5 outline-none" value={freq} onChange={(e) => setFreq(e.target.value)}>
                            <option value="H">Hourly View</option>
                            <option value="D">Daily View</option>
                            <option value="W">Weekly View</option>
                        </select>
                    </div>

                    {/* Filters */}
                    <div className="flex items-center gap-2 border-l pl-4 border-gray-200">
                        <Filter className="w-4 h-4 text-gray-400" />
                        <select className="bg-gray-50 border border-border text-sm font-medium rounded-xl p-2.5 outline-none max-w-[150px]" value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setProductId(''); }}>
                            <option value="">All Categories</option>
                            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                        <select className="bg-gray-50 border border-border text-sm font-medium rounded-xl p-2.5 outline-none max-w-[150px]" value={productId} onChange={(e) => setProductId(e.target.value)} disabled={!categoryId}>
                            <option value="">All Products</option>
                            {products.filter(p => !categoryId || p.category_id === parseInt(categoryId)).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                    </div>

                    {/* Compare Toggle */}
                    <div className="flex items-center gap-2 border-l pl-4 border-gray-200 ml-auto">
                        <label className="flex items-center cursor-pointer gap-2 select-none">
                            <div className="relative">
                                <input type="checkbox" className="sr-only" checked={isComparing} onChange={(e) => setIsComparing(e.target.checked)} />
                                <div className={clsx("block w-10 h-6 rounded-full transition-colors", isComparing ? "bg-primary" : "bg-gray-200")}></div>
                                <div className={clsx("absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform", isComparing ? "translate-x-4" : "")}></div>
                            </div>
                            <span className="text-sm font-medium text-gray-700">Compare Prev.</span>
                        </label>
                    </div>
                </div>

                {/* --- Tabs --- */}
                <div className="flex gap-4 border-b border-gray-200">
                    <button onClick={() => setActiveTab('historical')} className={clsx("pb-3 text-sm font-semibold transition-all border-b-2", activeTab === 'historical' ? "border-primary text-primary" : "border-transparent text-gray-400 hover:text-gray-700")}>
                        <TrendingUp className="w-4 h-4 inline-block mr-2" /> Historical Overview
                    </button>
                    <button onClick={() => setActiveTab('forecast')} className={clsx("pb-3 text-sm font-semibold transition-all border-b-2", activeTab === 'forecast' ? "border-primary text-primary" : "border-transparent text-gray-400 hover:text-gray-700")}>
                        <BrainCircuit className="w-4 h-4 inline-block mr-2" /> AI Forecasting
                    </button>
                </div>

                {/* --- Content Area --- */}
                {isLoading && !currData ? (
                    <div className="h-64 flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>
                ) : activeTab === 'historical' && currData ? (

                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <KpiCard title={`Total ${metric === 'revenue' ? 'Revenue' : 'Orders'}`}
                                value={valFormatter(currData.summary.total)}
                                prevValue={isComparing && prevData ? valFormatter(prevData.summary.total) : undefined}
                                icon={metric === 'revenue' ? <DollarSign className="w-6 h-6 text-green-600" /> : <ShoppingBag className="w-6 h-6 text-blue-600" />} />

                            <KpiCard title={`Average / ${freq === 'D' ? 'Day' : freq === 'H' ? 'Hour' : 'Week'}`}
                                value={valFormatter(currData.summary.avg)}
                                prevValue={isComparing && prevData ? valFormatter(prevData.summary.avg) : undefined}
                                icon={<TrendingUp className="w-6 h-6 text-orange-600" />} />

                            <KpiCard title="Maximum Peak"
                                value={valFormatter(currData.summary.max)}
                                prevValue={isComparing && prevData ? valFormatter(prevData.summary.max) : undefined}
                                icon={<BarChart3 className="w-6 h-6 text-purple-600" />} />

                            <KpiCard title="Minimum Drop"
                                value={valFormatter(currData.summary.min)}
                                prevValue={isComparing && prevData ? valFormatter(prevData.summary.min) : undefined}
                                icon={<Activity className="w-6 h-6 text-rose-600" />} />
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Main TimeSeries Chart */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-border lg:col-span-2 flex flex-col min-h-[400px]">
                                <h3 className="text-sm font-semibold mb-6 font-serif">Main Timeseries Trend</h3>
                                <div className="flex-1 w-full min-h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={tsChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                            <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} minTickGap={30} />
                                            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} tickFormatter={valFormatter} />
                                            <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} formatter={(val: any) => [valFormatter(val), '']} />
                                            <Legend verticalAlign="top" height={36} />
                                            <Line type="monotone" dataKey="Current" stroke="#000000" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#000000' }} />
                                            {isComparing && (
                                                <Line type="monotone" dataKey="Previous" stroke="#9CA3AF" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                                            )}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Top Products Table */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-border flex flex-col min-h-[400px]">
                                <h3 className="text-sm font-semibold mb-4 font-serif">Top Performing Products</h3>
                                <div className="flex-1 overflow-y-auto">
                                    <div className="space-y-4">
                                        {topProducts.map((p, idx) => (
                                            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center font-bold text-xs text-gray-400 border border-gray-100">
                                                        #{idx + 1}
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-semibold text-gray-900">{p.product_name}</p>
                                                        <p className="text-xs text-gray-500">{p.qty} items sold</p>
                                                    </div>
                                                </div>
                                                <div className="text-sm font-bold text-green-600">
                                                    {formatCurrency(p.revenue)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Breakdown Row */}
                        {!isComparing && currData.breakdown && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-white p-6 rounded-2xl shadow-sm border border-border h-72">
                                    <h3 className="text-sm font-semibold mb-6 flex items-center gap-2 font-serif"><Calendar className="w-4 h-4 text-gray-400" /> Average by Weekday</h3>
                                    <ResponsiveContainer width="100%" height="80%">
                                        <BarChart data={Object.entries(currData.breakdown.weekday_avg).map(([k, v]) => ({ name: k, value: v }))}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} />
                                            <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} formatter={(val: any) => [valFormatter(val), 'Avg']} />
                                            <Bar dataKey="value" fill="#000000" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>

                                {Object.keys(currData.breakdown.hour_avg).length > 0 && freq !== 'H' && freq !== 'W' && (
                                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-border h-72">
                                        <h3 className="text-sm font-semibold mb-6 flex items-center gap-2 font-serif"><Clock className="w-4 h-4 text-gray-400" /> Average by Hour of Day</h3>
                                        <ResponsiveContainer width="100%" height="80%">
                                            <BarChart data={Object.entries(currData.breakdown.hour_avg).map(([k, v]) => ({ name: `${k}:00`, value: v }))}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} minTickGap={20} />
                                                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} formatter={(val: any) => [valFormatter(val), 'Avg']} />
                                                <Bar dataKey="value" fill="#6B7280" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </div>
                        )}

                    </div>

                ) : activeTab === 'forecast' ? (

                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* Forecast Controls */}
                        <div className="bg-primary/5 p-6 rounded-2xl border border-primary/20 flex flex-wrap gap-6 items-center">
                            <div className="flex items-center gap-3">
                                <div className="p-3 bg-white rounded-xl shadow-sm">
                                    <BrainCircuit className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold">Predictive Engine</h2>
                                    <p className="text-sm text-muted-foreground">Train ML models on your filtered data</p>
                                </div>
                            </div>

                            <div className="flex gap-4 items-end ml-auto">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Algorithm</label>
                                    <select className="block w-40 bg-white border border-border text-sm font-medium rounded-xl p-2.5 outline-none shadow-sm" value={fcastModel} onChange={(e) => setFcastModel(e.target.value)}>
                                        <option value="xgboost">XGBoost</option>
                                        <option value="sklearn">Scikit-Learn (HGBR)</option>
                                        <option value="arima">Statsmodels (SARIMAX)</option>
                                    </select>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Horizon</label>
                                    <select className="block w-32 bg-white border border-border text-sm font-medium rounded-xl p-2.5 outline-none shadow-sm" value={fcastHorizon} onChange={(e) => setFcastHorizon(parseInt(e.target.value))}>
                                        <option value={7}>Next 7 steps</option>
                                        <option value={14}>Next 14 steps</option>
                                        <option value={30}>Next 30 steps</option>
                                    </select>
                                </div>
                                <button
                                    onClick={runForecast}
                                    disabled={fcastIsRunning}
                                    className="bg-primary text-primary-foreground px-6 py-2.5 rounded-xl font-semibold shadow-md hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-70 flex items-center gap-2"
                                >
                                    {fcastIsRunning ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Generate Forecast"}
                                </button>
                            </div>
                        </div>

                        {fcastResult && (
                            <>
                                {/* Validation Metrics */}
                                {fcastResult.backtest_metrics && (
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="bg-white p-5 rounded-2xl shadow-sm border border-border">
                                            <p className="text-xs font-bold tracking-wider text-gray-400 mb-1">MEAN ABSOLUTE ERROR (MAE)</p>
                                            <p className="text-2xl font-bold font-serif">{valFormatter(fcastResult.backtest_metrics.avg_MAE)}</p>
                                            <p className="text-xs text-gray-400 mt-1">Average deviation per step</p>
                                        </div>
                                        <div className="bg-white p-5 rounded-2xl shadow-sm border border-border">
                                            <p className="text-xs font-bold tracking-wider text-gray-400 mb-1">ROOT MEAN SQUARED ERROR</p>
                                            <p className="text-2xl font-bold font-serif">{valFormatter(fcastResult.backtest_metrics.avg_RMSE)}</p>
                                            <p className="text-xs text-gray-400 mt-1">Penalizes large outlier errors</p>
                                        </div>
                                        <div className="bg-white p-5 rounded-2xl shadow-sm border border-border">
                                            <p className="text-xs font-bold tracking-wider text-gray-400 mb-1">MEAN ABSOLUTE % ERROR (MAPE)</p>
                                            <p className="text-2xl font-bold font-serif">{(fcastResult.backtest_metrics.avg_MAPE * 100).toFixed(1)}%</p>
                                            <p className="text-xs text-gray-400 mt-1">Percentage accuracy variation</p>
                                        </div>
                                    </div>
                                )}

                                {/* Forecast Chart */}
                                <div className="bg-white p-6 rounded-2xl shadow-sm border border-border flex flex-col min-h-[500px]">
                                    <div className="flex justify-between items-center mb-6">
                                        <h3 className="text-lg font-serif">
                                            <span className="font-bold">{fcastResult.model_info}</span> Projection
                                        </h3>
                                        <span className="text-xs font-mono bg-gray-100 px-3 py-1 rounded-full text-gray-500">
                                            Trained on {fcastResult.fitted_range.points} points ({fcastResult.fitted_range.start.split(' ')[0]} - {fcastResult.fitted_range.end.split(' ')[0]})
                                        </span>
                                    </div>
                                    <div className="flex-1 w-full min-h-[400px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <ComposedChart data={forecastChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} minTickGap={40} />
                                                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} tickFormatter={valFormatter} />
                                                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} formatter={(val: any, name: any) => [valFormatter(val), name === 'range' ? 'Confidence Interval' : name]} />
                                                <Legend verticalAlign="top" height={36} />

                                                {/* Confidence Interval shaded band — upper area first, then fill down to lower */}
                                                <Area type="monotone" dataKey="upper" stroke="none" fill="#3B82F6" fillOpacity={0.15} legendType="none" tooltipType="none" />
                                                <Area type="monotone" dataKey="lower" stroke="none" fill="#ffffff" fillOpacity={1} legendType="none" tooltipType="none" />

                                                <Line type="monotone" dataKey="Actual" stroke="#111827" strokeWidth={2} dot={false} />
                                                <Line type="monotone" dataKey="Forecast" stroke="#2563EB" strokeWidth={2.5} strokeDasharray="6 3" dot={false} activeDot={{ r: 6, fill: '#2563EB' }} />
                                            </ComposedChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </>
                        )}

                        {!fcastResult && !fcastIsRunning && (
                            <div className="h-64 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-2xl opacity-60">
                                <BrainCircuit className="w-12 h-12 text-gray-300 mb-3" />
                                <p className="font-medium text-gray-500">Select your parameters and click Generate Forecast to begin AI backtesting.</p>
                            </div>
                        )}
                    </div>
                ) : null}

            </div>
        </div>
    );
}

// Reusable KPI Component
function KpiCard({ title, value, prevValue, icon }: { title: string, value: string, prevValue?: string, icon: React.ReactNode }) {

    let isUp = false;
    let isDown = false;
    let percentStr = "";

    if (prevValue) {
        const cVal = parseFloat(value.replace(/[^0-9.-]+/g, ""));
        const pVal = parseFloat(prevValue.replace(/[^0-9.-]+/g, ""));
        if (pVal !== 0 && !isNaN(cVal) && !isNaN(pVal)) {
            const diff = cVal - pVal;
            const pct = (diff / pVal) * 100;
            isUp = pct > 0;
            isDown = pct < 0;
            percentStr = Math.abs(pct).toFixed(1) + "%";
        }
    }

    return (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-border flex items-center justify-between hover:shadow-md transition-shadow">
            <div>
                <p className="text-sm font-semibold text-muted-foreground">{title}</p>
                <div className="flex items-baseline gap-2 mt-1">
                    <p className="text-2xl font-bold font-serif text-gray-900">{value}</p>
                    {prevValue && (
                        <span className={clsx("text-xs font-bold px-2 py-0.5 rounded-full", isUp ? "bg-green-100 text-green-700" : isDown ? "bg-rose-100 text-rose-700" : "bg-gray-100 text-gray-500")}>
                            {isUp ? "↑" : isDown ? "↓" : "−"} {percentStr || "0%"}
                        </span>
                    )}
                </div>
                {prevValue && <p className="text-xs text-gray-400 mt-1">vs {prevValue}</p>}
            </div>
            <div className="w-12 h-12 rounded-full bg-gray-50/80 border border-gray-100 flex items-center justify-center flex-shrink-0">
                {icon}
            </div>
        </div>
    );
}
