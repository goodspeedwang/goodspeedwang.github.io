// ============================================================
//  Pocket Money Account · Ledger Data
//  Only edit this file. Save it and refresh piggybank.html to update.
// ============================================================

window.PIGGYBANK_DATA = {
  // 手动流水：
  //   amount 为正数（或写 type:'income' 的正数） → 支出（余额减少）
  //   amount 为负数                        → 手动存钱 / 入账（余额增加其绝对值）
  //   例：{ date:'2026-10-23', amount:-300, note:'游学零花' } 表示存入 300
  transactions: [

    { date: '2026-10-24', amount: 8.97, note: '主食厨房' },
    { date: '2026-10-23', amount: -300, note: '游学零花' },
    { date: '2026-10-23', amount: 10.87, note: '泉盛果蔬大屯店' },
    { date: '2026-10-23', amount: 26.26, note: '芯果科技' },
    { date: '2026-10-05', amount: 2.94, note: '' },
    { date: '2026-10-05', amount: 39.94, note: '宜家' },
  ],

  //#region ---------- Settings (change as needed) ----------
  config: {
    startDate: '2026-10-05',   // account opening date (allowance starts from the 1st of this month)
    initialBalance: 44.45,         // money already in the account when opened (use 0 if none)

    // Schedule: ALL settings live here. Each entry takes effect FROM its 'date'
    // (format 'YYYY-MM' or 'YYYY-MM-DD') and overrides the previous one. Between two
    // dates, the EARLIER entry's config is used. The first entry is the baseline
    // (its date should be on/before the opening date).
    // Per-entry fields (all optional except date):
    //   monthlyAllowance, annualInterestRate, holidayAllowance
    //   holidayAllowance is a single number deposited on the 1st of each month
    //   (0 = no extra holiday allowance that month).
    // Example:
    //   schedule: [
    //     { date: '2026-10', monthlyAllowance: 100, annualInterestRate: 0.02, holidayAllowance: 0 },
    //     { date: '2027-07', holidayAllowance: 50 },   // July: +50 holiday allowance
    //     { date: '2027-08', holidayAllowance: 0 }     // August: back to none
    //   ]
    schedule: [
      { date: '2026-10', monthlyAllowance: 100, annualInterestRate: 0.02,holidayAllowance: 0 },
    ]
  }
  //#endregion
};
