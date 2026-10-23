// ============================================================
//  Pocket Money Account · Ledger Data
//  Only edit this file. Save it and refresh piggybank.html to update.
// ============================================================

window.PIGGYBANK_DATA = {
  transactions: [
    
    { date: '2026-10-23', amount: 10.87, note: '泉盛果蔬大屯店' },
    { date: '2026-10-23', amount: 26.26, note: '芯果科技' },
    { date: '2026-10-05', amount: 2.94, note: '' },
    { date: '2026-10-05', amount: 39.94, note: '宜家' },
  ],

  // ---------- Settings (change as needed) ----------
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
      { date: '2026-10', monthlyAllowance: 100, annualInterestRate: 0.02, holidayAllowance: 0 },
      { date: '2026-11', holidayAllowance: 300 }, //游学零花
      { date: '2026-12', holidayAllowance: 0 }, 
    ]
  }
};
