class Button {
    constructor(rank, suit){
        this.rank = rank
        this.suit = suit
        this.card = [rank, suit]
        this.button = $('<button>');
        
        this.state = 'unselected'
        this.colour = this.suit=='d'||this.suit=='h'?'#eb4034':'#000000'
        
        this.button.addClass('card')
        this.button.text(this.rank + this.suit);
        this.updateColour()
        
        this.button.hover(()=>{this.button.css('background-color', suit=='d'||suit=='h'?'#e37171':'#363636')}, this.updateColour.bind(this))
        
        this.button.click(this.click.bind(this))
    }
    click(event){
        if (this.state==='unselected') {
            this.state = 'holeCard'
            holeCards.add(this.card)
        } else if (this.state==='holeCard') {
            holeCards.remove(this.card)
            flopCards.add(this.card)
            this.state = 'flopCard'
        } else if (this.state==='flopCard') {
            flopCards.remove(this.card)
            turnCards.add(this.card)
            this.state = 'turnCard'
        } else if (this.state==='turnCard') {
            turnCards.remove(this.card)
            riverCards.add(this.card)
            this.state = 'riverCard'
        } else if (this.state==='riverCard'){
            riverCards.remove(this.card)
            this.state = 'unselected'
            this.colour = this.suit=='d'||this.suit=='h'?'#eb4034':'#000000'
        }
        this.updateColour()
    }
    
    updateColour(){
        if (this.state==='unselected') {
            this.colour = this.suit=='d'||this.suit=='h'?'#eb4034':'#000000'
        } else if (this.state==='holeCard') {
            this.colour = 'green'
        } else if (this.state==='flopCard') {
            this.colour = '#4290f5'
        } else if (this.state==='turnCard') {
            this.colour = '#486dab'
        } else if (this.state==='riverCard'){
            this.colour = '#3f4b99'
        }
        this.button.css('background-color', this.colour)
    }
    
    setState(state){
        this.state = state
    }
    
    getElement(){
        return this.button
    }
}
class Cards{
    constructor(){
        this.cards = []
    }
    add(x){
        this.cards.push(x)
    }
    remove(x){
        const index = this.cards.indexOf(x)
        if (index !== -1) this.cards.splice(index, 1)
    }
    clear(){
        this.cards = []
    }
    getCards(){
        return this.cards
    }
}

holeCards = new Cards()
flopCards = new Cards()
turnCards = new Cards()
riverCards = new Cards()

suitDict = {0:'s', 1:'c', 2:'h', 3:'d'}
rankDict = {0:'2', 1:'3', 2:'4', 3:'5', 4:'6', 5:'7', 6:'8', 7:'9', 8:'T', 9:'J', 10:'Q', 11:'K', 12:'A'}

master = $('.buttonContainer')
columns = $('<div class=buttonContainer>')

buttons = []

for (let i = 0; i < 4; i++) {
    buttons[i] = []
    suit = suitDict[i];
    column = $(`<div class="suitColumn">`)
    for (let j = 0; j < 13; j++) {
        rank = rankDict[j];
        button = new Button(rank, suit)
        buttons[i][j] = button

        column.append(button.getElement())
    }
    columns.append(column)
}
master.append(columns)


master = $('.cardInput')
resetButton = $('<button>')
resetButton.text('reset')
resetButton.addClass('reset')
resetButton.css('background-colour', '#808080')
resetButton.hover(()=>{resetButton.css('background-colour', '#9c9c9c')},
            ()=>{resetButton.css('background-colour', '#808080')})
resetButton.click(()=>{
    holeCards.clear();
    flopCards.clear();
    turnCards.clear();
    riverCards.clear()
    buttons.forEach(suitColumn => {
        suitColumn.forEach(card => {
            card.setState('unselected')
            card.updateColour()
        })
    })
})
master.append(resetButton)