const API_URL = 'https://rickandmortyapi.com/api/character';

        const characterGrid = document.getElementById('characterGrid');

        async function fetchCharacters(){

            const response = await fetch(API_URL);
            const data = await response.json();

            // console.log(data)

            displayCharacters(data.results)

        }


        function displayCharacters(characters){

            // console.log(characters)

            // for(let i = 0; i < 10; i++){ // for i in range(10)
            //     console.log(`${i}`)
            // }


            // for character in characters:
            //   print(character)

            characterGrid.innerHTML = '';

            characters.forEach(character => {

                const cardHTML = `
                    <div class="card" style="width: 18rem;">
                        <img src="${character.image}" class="card-img-top" alt="...">
                        <div class="card-body">
                            <h5 class="card-title">${character.name}</h5>
                            <p class="card-text">Created: ${character.created}</p>
                            <p class="card-text">Speacies: ${character.speacies}</p>
                            <p class="card-text">Status: ${character.status}</p>
                            <a href="#" class="btn btn-primary">Go somewhere</a>
                        </div>
                    </div>
                `;
                
                // console.log(character)
                // console.log(cardHTML)


                characterGrid.innerHTML += cardHTML;
            });


        }

        fetchCharacters()