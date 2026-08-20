const puppeteer = require('puppeteer');
const express = require('express');
const fs = require('fs');
const fetch = require('node-fetch');
require('dotenv').config()


const server = express();


server.get('/', function(req, res) {


const chromeOptions = {
  slowMo: 90,
  headless: false,
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
  ]
};


async function bot(){
  const browser = await puppeteer.launch(chromeOptions);
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 })
  await page.goto('https://www.workana.com/login?ref=home_header');
  
  
  

  await page.type('input[type="email"]', process.env.DB_USER)
  await page.type('input[type="password"]', process.env.DB_PASS)

  await page.click('button[type="submit"]');

  
  await page.goto('https://www.workana.com/jobs?language=pt&skills=android%2Ccss3%2Chtml5%2Cjavascript%2Cmobile-app-design-1%2Cmysql%2Cphp%2Cpostgressql%2Cpython%2Creact-native%2Cresponsive-web-design%2Csql');
  await page.waitForNavigation()  
  let listValues = await page.evaluate(() => {
    let allDetails = document.querySelectorAll('[data-text-expand="Ver mais detalhes"]')

    let titles = document.querySelectorAll('span[title]')
    
    let values = document.querySelectorAll('span.values')
    
    let bids = document.querySelectorAll('span.bids')

    const ListTitles = [...titles]
    const ListValues = [...values]
    const ListBids = [...bids]
    const ListAllDetails = [...allDetails]

    const resultTitles = ListTitles.map((title) =>  String(title.innerText));
    const resultValues = ListValues.map((value) =>  String(value.innerText));
    const resultBids = ListBids.map((bid) =>  String(bid.innerText));
    const resultDetails = ListAllDetails.map((detail) =>  String(detail.innerText));

    

    return {resultTitles,resultValues,resultBids,resultDetails}
    });

    var result = ' '
    for(let i=0; i<= listValues.resultTitles.length;i++){
      if(listValues.resultTitles[i] !== 'Titulo:'){
        result += `<div>Titulo: ${listValues.resultTitles[i]} <br/> ${listValues.resultTitles[i+1]} <br/> Valor: ${listValues.resultValues[i]} <br/> Propostas: ${listValues.resultBids[i]} <br/> Detalhes: ${listValues.resultDetails[i]} <br/><br/></div><hr/>`
      }
    }

  
    res.send(result)
    //await browser.close();
}


bot()

})


server.listen(process.env.PORT, () => console.log('rodando'))
