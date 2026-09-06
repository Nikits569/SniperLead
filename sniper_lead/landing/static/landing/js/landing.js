document.addEventListener('alpine:init', () => {
  Alpine.data('heroTerminal', () => ({
    activeTab: 'rent',
    isAnimating: false,
    switchTab(tab) {
      if (this.activeTab === tab) return;
      this.isAnimating = true;
      setTimeout(() => {
        this.activeTab = tab;
        this.isAnimating = false;
      }, 150);
    },
    leads: {
      rent: { source: 'FB: Bývanie a prenájom BA', time: 'pred 8s', title: 'Hľadáme 2-izbák v Ružinove', text: '«Pracujúci pár hľadá 2-izbový byt. Rozpočet 850€ so všetkým, ideálne s parkovaním...»', profit: '+ 850 €', profitSub: 'Provízia z prenájmu', score: '98', btn: 'Volať klientovi' },
      vnz: { source: 'TG: Imigrácia Slovensko', time: 'pred 14s', title: 'Termín na cudzineckú políciu', text: '«Súrne hľadám pomoc s termínom na polícii v BA a prekladom dokumentov na živnosť...»', profit: '+ 450 €', profitSub: 'Právna asistencia', score: '96', btn: 'Napísať klientovi' },
      build: { source: 'FB: Majstri a rekonštrukcie', time: 'pred 22s', title: 'Obklad kúpeľne 7m²', text: '«Hľadám obkladača na kúpeľňu. Materiál kúpený na mieste, platba ihneď po dokonчении.»', profit: '+ 1 200 €', profitSub: 'Zákazka pre majstra', score: '95', btn: 'Volať zákazníkovi' },
      auto: { source: 'FB: Autičkári Východ', time: 'pred 35s', title: 'Keramická ochrana BMW', text: '«Kto má termín do piatku na leštenie laku a 3-ročnú keramiku? Košice a okolie...»', profit: '+ 380 €', profitSub: 'Detailing balík', score: '93', btn: 'Otvoriť FB profil' }
    }
  }));

Alpine.data('categoriesHub', () => ({
    selected: 'all',
    // Подтягиваем переведенный массив из глобальной переменной HTML
    cats: window.LANDING_CATS || [],

    get filteredCats() {
      return this.selected === 'all'
        ? this.cats
        : this.cats.filter(c => c.g === this.selected);
    }
  }));

  Alpine.data('roiCalculator', () => ({
    margin: 150,
    leads: 2,
    cost: 49,
    get profit() {
      return Math.max(0, (this.margin * this.leads) - this.cost);
    }
  }));
});