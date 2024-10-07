<template>
    <div class="trending-table">
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th rowspan="2">年份</th>
                        <th v-for="month in months" :key="month">{{ month }}</th>
                    </tr>
                </thead>
                <tbody>
                    <template v-for="year in years" :key="year">
                        <tr>
                            <td>{{ year }}</td>
                            <template v-for="(value, monthIndex) in getYearData(year)" :key="year + '-month-' + monthIndex">
                                <td>{{ valueDisplay(value) }}</td>
                            </template>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        data: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            yearData: {}
        };
    },
    computed: {
        months() {
            return ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
        },
        years() {
            const startYear = new Date(this.data.時間起點).getFullYear();
            const endYear = new Date(this.data.時間終點).getFullYear();
            let years = [];
            for (let year = startYear; year <= endYear; year++) {
                years.push(year);
            }
            return years;
        },
    },
    methods: {
        getYearData(year) {
            return this.yearData[year];
        },
        processInitData() {
            const startMonth = new Date(this.data.時間起點).getMonth() + 1;
            const endMonth = new Date(this.data.時間終點).getMonth() + 1;
            const startYear = new Date(this.data.時間起點).getFullYear();
            const endYear = new Date(this.data.時間終點).getFullYear();
            this.yearData = {};
            for (let year = startYear; year <= endYear; year++) {
                let yearPrices = [];
                for (let month = 1; month <= 12; month++) {
                    if (year === startYear && month < startMonth) {
                        yearPrices.push('0');
                    } else if (year === endYear && month > endMonth) {
                        yearPrices.push('0');
                    } else {
                        yearPrices.push(this.data.統計值.split(',')[month + (year - startYear) * 12 - startMonth]);
                    }
                }
                this.yearData[year] = yearPrices;
            }
        },
        valueDisplay(value) {
            return value === '0' ? '-' : value;
        }
    },
    watch: {
        data: {
            deep: true,
            handler(newVal) {
                if (newVal) {
                    this.processInitData();
                }
            }
        }
    },
    created() {
        this.processInitData();
    }
};
</script>

<style scoped>
.trending-table {
    margin-top: 2em;
    width: 100%;
    overflow-x: auto;
}

.table-wrapper {
    min-width: 800px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    border: 1px solid #ccc;
    padding: 0.5em;
    text-align: center;
}

@media screen and (max-width: 768px) {
    .trending-table {
        font-size: 14px;
    }

    th,
    td {
        padding: 0.3em;
    }
}

@media screen and (max-width: 480px) {
    .trending-table {
        font-size: 12px;
    }

    th,
    td {
        padding: 0.2em;
    }
}
</style>