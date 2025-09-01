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
                        restitution: 0.1,
                        friction: 0.1,
                        render: { fillStyle: "#c9a36c" }
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
});
