document.addEventListener("DOMContentLoaded", () => {
    const { Engine, Render, Runner, World, Bodies, Mouse, MouseConstraint } = Matter;

    const engine = Engine.create();
    const world = engine.world;

    const canvas = document.getElementById("caixas");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const render = Render.create({
        canvas: canvas,
        engine: engine,
        options: {
            width: window.innerWidth,
            height: window.innerHeight,
            background: "transparent",
            wireframes: false
        }
    });

    Render.run(render);
    Runner.run(Runner.create(), engine);

    const paredes = [
        Bodies.rectangle(window.innerWidth / 2, window.innerHeight + 20, window.innerWidth, 40, { isStatic: true }),
        Bodies.rectangle(window.innerWidth / 2, -20, window.innerWidth, 40, { isStatic: true }),
        Bodies.rectangle(-20, window.innerHeight / 2, 40, window.innerHeight, { isStatic: true }),
        Bodies.rectangle(window.innerWidth + 20, window.innerHeight / 2, 40, window.innerHeight, { isStatic: true }),
    ];
    World.add(world, paredes);

    function criarPilha(x, y, linhas, colunas) {
        const tamanho = 80;
        const espaco = 3;

        for (let i = 0; i < linhas; i++) {
            for (let j = 0; j < colunas; j++) {
                const box = Bodies.rectangle(
                    x + j * (tamanho + espaco),
                    y - i * (tamanho + espaco),
                    tamanho,
                    tamanho,
                    {
                        restitution: 0.3,
                        friction: 0.3,
                        render: { fillStyle: "#ffcd88ff" }
                    }
                );
                World.add(world, box);
            }
        }
    }
    

    criarPilha(10, window.innerHeight - 20, 5, 3);
    criarPilha(window.innerWidth - 150, window.innerHeight - 20, 5, 3);
    

    const mouse = Mouse.create(canvas);
    const mouseConstraint = MouseConstraint.create(engine, {
        mouse,
        constraint: { stiffness: 0.1, render: { visible: false } }
    });
    World.add(world, mouseConstraint);

    render.mouse = mouse;
       const loginBox = document.querySelector(".login-container"); // <- seu id do login
    const rect = loginBox.getBoundingClientRect();
    const canvasRect = canvas.getBoundingClientRect();

    // converte posição do login box para dentro do canvas
    const x = rect.left - canvasRect.left;
    const y = rect.top - canvasRect.top;

    const thickness = 20; // espessura das paredes invisíveis

    const paredesLogin = [
        // chão
        Bodies.rectangle(x + rect.width / 2, y + rect.height, rect.width, thickness, { isStatic: true, render: { visible: false } }),
        // esquerda
        Bodies.rectangle(x, y + rect.height / 2, thickness, rect.height, { isStatic: true, render: { visible: false } }),
        // direita
        Bodies.rectangle(x + rect.width, y + rect.height / 2, thickness, rect.height, { isStatic: true, render: { visible: false } }),
        // teto (opcional) — comente se quiser que as caixas possam entrar por cima
        // Bodies.rectangle(x + rect.width / 2, y, rect.width, thickness, { isStatic: true, render: { visible: false } }),
    ];

    World.add(world, paredesLogin);

});
