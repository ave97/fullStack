document.addEventListener('DOMContentLoaded', function () {
    const wheelSize = Math.min(window.innerWidth, 630);

    const center = wheelSize / 2;
    const radius = wheelSize / 2;

    const wheelContainer = document.getElementById('wheel-container');
    const wheelWrapper = document.querySelector('.wheel-wrapper');
    const wheel = document.getElementById('wheel');

    wheelContainer.style.width = wheelSize + 'px';
    wheelContainer.style.height = wheelSize + 'px';
    wheelWrapper.style.width = wheelSize + 'px';
    wheelWrapper.style.height = wheelSize + 'px';
    wheel.setAttribute('width', wheelSize);
    wheel.setAttribute('height', wheelSize);

    const wheelGroup = document.getElementById('wheel-group');
    wheelGroup.style.transform = 'rotate(0deg)';
    wheelGroup.getBoundingClientRect();

    const colors = ['#FFB6C1', '#FFD700', '#90EE90', '#87CEFA', '#FF7F50', '#DA70D6'];
    const labels = [
        '10', '10', '10',
        '20', '20', '20',
        '30', '30', '30',
        '50', '50',
        '100',
        '-20', '-20',
        'Bomb'
    ];

    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    shuffle(labels);

    const slices = [];

    // window.wheelSetup = {
    //     wheelGroup,
    //     labels,
    //     sliceAngle: 360 / labels.length,
    //     numberOfSlices: labels.length
    // };

    // Φτιάχνουμε τα slices και τα labels
    for (let i = 0; i < labels.length; i++) {
        const slice = document.createElementNS("http://www.w3.org/2000/svg", "path");

        const startAngle = (i * (360 / labels.length)) * (Math.PI / 180);
        const endAngle = ((i + 1) * (360 / labels.length)) * (Math.PI / 180);

        const x1 = center + radius * Math.cos(startAngle);
        const y1 = center + radius * Math.sin(startAngle);
        const x2 = center + radius * Math.cos(endAngle);
        const y2 = center + radius * Math.sin(endAngle);

        const d = `M${center},${center} L${x1},${y1} A${radius},${radius} 0 0,1 ${x2},${y2} Z`;

        slice.setAttribute('d', d);
        slice.setAttribute('fill', colors[i % colors.length]);
        slices.push(slice);
        wheelGroup.appendChild(slice);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");

        const midAngle = (startAngle + endAngle) / 2;
        const labelRadius = radius * 0.6;
        const textX = center + labelRadius * Math.cos(midAngle);
        const textY = center + labelRadius * Math.sin(midAngle);
        const rotation = (midAngle * 180 / Math.PI);

        text.setAttribute('x', textX);
        text.setAttribute('y', textY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', wheelSize / 20);
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', '#000');
        text.setAttribute('transform', `rotate(${rotation} ${textX} ${textY})`);
        text.textContent = labels[i];

        wheelGroup.appendChild(text);
    }

    window.wheelSetup = {
        wheelGroup,
        labels,
        sliceAngle: 360 / labels.length,
        numberOfSlices: labels.length,
        slices: slices // 🛑 ΕΔΩ προσθέτεις και τα slices!
    };
});
