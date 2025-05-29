<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHP Connection Example</title>
    <link rel="stylesheet" href="css/styles.css">
    <script defer src="js/script.js"></script>
</head>
<body>

    <h1>Connect PHP with HTML, CSS, and JavaScript</h1>

    <form id="dataForm">
        <input type="text" name="name" id="name" placeholder="Enter your name" required>
        <button type="submit">Submit</button>
    </form>

    <div id="response"></div>

    <?php
        // This will execute when the page loads
        echo "<p>This is PHP embedded in HTML.</p>";
    ?>

</body>
</html>
