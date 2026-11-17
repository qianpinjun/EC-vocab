// Virtual Puppy Module

const PetModule = {
    pet: null,
    speechTimer: null,

    dialogues: {
        idle: [
            "汪！主人今天背单词了吗？",
            "本汪正在默默给主人的大脑施加词汇记忆Buff！汪！",
            "刚才那个离谱小故事太搞笑了汪！",
            "听说全对通关可以拿到 100 枚金币大奖呢！",
            "只要每天坚持背一点，本汪就能快快升级啦~"
        ],
        hungry: [
            "呜呜……主人，本汪肚子咕咕叫了，求喂好吃的！",
            "快做几道情境题赚点金币吧，我想吃多汁牛排 🥩！",
            "饿得耳朵都搭拉下来了汪……"
        ],
        happy: [
            "汪汪汪！太好吃了！主人最好了！",
            "尾巴摇得停不下来啦！本汪活力拉满！",
            "芜湖！升级打怪，成为背词榜第一小狗！"
        ]
    },

    init() {
        this.bindEvents();
        this.loadPet();
        this.startDialogueLoop();
    },

    bindEvents() {
        const foodButtons = document.querySelectorAll('.btn-feed');
        foodButtons.forEach(btn => {
            btn.addEventListener('click', async () => {
                const itemKey = btn.getAttribute('data-item');
                await this.feedOrPlay(itemKey);
            });
        });

        // Click puppy for bark and pet interaction
        const puppySvg = document.getElementById('puppySvg');
        if (puppySvg) {
            puppySvg.addEventListener('click', () => {
                this.triggerPetReaction();
            });
        }
    },

    async loadPet() {
        try {
            const res = await API.pet.getPet();
            if (res.success && res.pet) {
                this.pet = res.pet;
                this.renderPetUI();
            }
        } catch (e) {
            console.error('Failed to load pet:', e);
        }
    },

    renderPetUI() {
        if (!this.pet) return;

        // Name & Level
        const nameDisplay = document.getElementById('petNameDisplay');
        const levelBadge = document.getElementById('petLevelBadge');
        if (nameDisplay) nameDisplay.textContent = this.pet.name || '旺财';
        
        const levelTitles = [
            'Lv. 1 萌新柴犬 🐶',
            'Lv. 2 聪明好学犬 🐾',
            'Lv. 3 词汇探险犬 🎒',
            'Lv. 4 学霸柯基犬 🎓',
            'Lv. 5 银河至尊神犬 🌟'
        ];
        const title = levelTitles[Math.min(this.pet.level - 1, levelTitles.length - 1)] || `Lv. ${this.pet.level} 宇宙超级神犬`;
        if (levelBadge) levelBadge.textContent = title;

        // Meters
        const hunger = Math.max(0, Math.min(100, this.pet.hunger));
        const happy = Math.max(0, Math.min(100, this.pet.happiness));
        const expNeeded = this.pet.level * 100;
        const exp = this.pet.exp;

        document.getElementById('petHungerText').textContent = `${hunger}%`;
        document.getElementById('petHungerFill').style.width = `${hunger}%`;

        document.getElementById('petHappyText').textContent = `${happy}%`;
        document.getElementById('petHappyFill').style.width = `${happy}%`;

        document.getElementById('petExpText').textContent = `${exp} / ${expNeeded}`;
        const expPercent = Math.min(100, Math.round((exp / expNeeded) * 100));
        document.getElementById('petExpFill').style.width = `${expPercent}%`;

        // Update speech if hungry
        if (hunger < 30) {
            this.setSpeech(this.randomItem(this.dialogues.hungry));
        }
    },

    async feedOrPlay(itemKey) {
        try {
            const res = await API.pet.interact(itemKey);
            showToast(res.message, 'success');

            // Play eating sfx & chew animation
            sounds.playBark();
            const puppyGroup = document.getElementById('puppyGroup');
            if (puppyGroup) {
                puppyGroup.classList.remove('puppy-chew');
                void puppyGroup.offsetWidth; // trigger reflow
                puppyGroup.classList.add('puppy-chew');
            }

            // Update user coins globally
            const userCoinsElem = document.getElementById('userCoins');
            const petUserCoinsElem = document.getElementById('petUserCoins');
            if (userCoinsElem) userCoinsElem.textContent = res.user_coins;
            if (petUserCoinsElem) petUserCoinsElem.textContent = res.user_coins;

            // Update pet state
            this.pet.hunger = res.result.hunger;
            this.pet.happiness = res.result.happiness;
            this.pet.exp = res.result.exp;
            this.pet.level = res.result.level;

            this.renderPetUI();
            this.setSpeech(this.randomItem(this.dialogues.happy));

            if (res.result.leveled_up) {
                showToast(`🎉 恭喜！小狗旺财升级到 Lv. ${this.pet.level}！`, 'success');
                sounds.playVictory();
            }
        } catch (e) {
            showToast(e.message, 'warning');
        }
    },

    triggerPetReaction() {
        sounds.playBark();
        const puppyGroup = document.getElementById('puppyGroup');
        if (puppyGroup) {
            puppyGroup.classList.add('puppy-chew');
            setTimeout(() => puppyGroup.classList.remove('puppy-chew'), 1000);
        }
        this.setSpeech("汪！被主人摸头好舒服！今天也要一起加油背单词汪！❤️");
    },

    setSpeech(text) {
        const bubble = document.getElementById('petSpeechBubble');
        if (bubble) {
            bubble.textContent = text;
        }
    },

    startDialogueLoop() {
        if (this.speechTimer) clearInterval(this.speechTimer);
        this.speechTimer = setInterval(() => {
            if (this.pet && this.pet.hunger < 30) {
                this.setSpeech(this.randomItem(this.dialogues.hungry));
            } else {
                this.setSpeech(this.randomItem(this.dialogues.idle));
            }
        }, 12000);
    },

    randomItem(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }
};

window.PetModule = PetModule;
