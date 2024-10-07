<template>
    <div class="chart-container">
        <canvas id="trendingChart"></canvas>
    </div>
</template>

<script>
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

export default {
    props: ['data'],
    data() {
        return {
            chart: null
        }
    },
    mounted() {
        this.createChart(this.data);
        window.addEventListener('resize', this.handleResize);
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    },
    watch: {
        data(newData, oldData) {
            if (newData !== oldData) {
                this.createChart(newData);
            }
        }
    },
    methods: {
        createChart(data) {
            if (this.chart) {
                this.chart.destroy();
            }
            const ctx = document.getElementById('trendingChart').getContext('2d');
            let prices = data.統計值.split(',').map(price => parseInt(price, 10));
            let labels = this.generateLabels(data.時間起點, data.時間終點, prices.length);

            // 處理前導0並調整起始標籤
            let firstNonZeroIndex = prices.findIndex(price => price !== 0);
            if (firstNonZeroIndex > 0) {
                prices = prices.slice(firstNonZeroIndex);
                labels = labels.slice(firstNonZeroIndex);
            }

            // 替換中間的0並記錄點的位置來標註
            let lastValidPrice = prices[0];
            const annotations = [];
            prices = prices.map((price, index) => {
                if (price === 0) {
                    annotations.push({ index, price: lastValidPrice });
                    return lastValidPrice;
                }
                lastValidPrice = price;
                return price;
            });

            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: data.產品名稱,
                        data: prices,
                        fill: false,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        pointRadius: prices.map((_, index) => annotations.some(a => a.index === index) ? 5 : 3),
                        pointStyle: prices.map((_, index) => annotations.some(a => a.index === index) ? 'crossRot' : 'circle'), // 無資料點-使用cross標註
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    },
                    animation: {
                        duration: 300,
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                        }
                    }
                }
            });
        },

        generateLabels(startDate, endDate, count) {
            const start = new Date(startDate);
            const labels = [];
            for (let i = 0; i < count; i++) {
                const monthDate = new Date(start.getFullYear(), start.getMonth() + i, 1);
                labels.push(`${monthDate.getFullYear()}.${monthDate.getMonth() + 1}`.padStart(2, '0'));
            }
            return labels;
        },

        handleResize() {
            if (this.chart) {
                this.chart.resize();
            }
        }
    }
};
</script>

<style scoped>
.chart-container {
    position: relative;
    margin: auto;
    height: 30vh;
    width: 100%;
    max-width: 1200px;
}

@media (max-width: 768px) {
    .chart-container {
        height: 50vh;
    }
}

@media (max-width: 480px) {
    .chart-container {
        height: 60vh;
    }
}
</style>